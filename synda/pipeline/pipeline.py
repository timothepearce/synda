from functools import wraps
from typing import TYPE_CHECKING, Optional

from rich.console import Console
from rich.markup import escape
from sqlmodel import Session

from synda.database import engine
from synda.model.run import Run, RunStatus
from synda.model.step import Step
from synda.utils.env import is_debug_enabled

if TYPE_CHECKING:
    from synda.config import Config

CONSOLE = Console()


class Pipeline:
    def __init__(self, config: Optional["Config"] = None):
        self.session = Session(engine)
        self.config = config
        self.input_loader = config.input.get_loader() if config else None
        self.output_saver = config.output.get_saver() if config else None
        self.pipeline = config.pipeline if config else None
        self.run = Run.create_with_steps(self.session, config) if config else None

    @staticmethod
    def handle_run_errors(func):
        """Decorator to handle run errors gracefully."""
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                if self.run is not None:
                    self.run.update(self.session, RunStatus.ERRORED)
                raise e
        return wrapper

    @staticmethod
    def handle_stop_option(func):
        """Decorator to handle user interruption (Ctrl+C) during execution."""
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except KeyboardInterrupt:
                if self.run is not None:
                    prompt = f"\nAre you sure you want to stop the run {self.run.id}? [y/N]: "
                    escaped_prompt = escape(prompt)

                    user_input = CONSOLE.input(f"[red]{escaped_prompt}[/]").strip().lower()

                    if user_input == 'y':
                        self.run.update(self.session, RunStatus.STOPPED)
                        CONSOLE.print(f"[blue]Run with id {self.run.id} is stopped.\nTo resume the run, use:")
                        CONSOLE.print(f"[cyan]synda generate --resume {self.run.id}")
                        exit(0)
                    else:
                        self.resume(run_id=self.run.id)
        return wrapper

    @handle_run_errors
    @handle_stop_option
    def execute(self):
        if self.config is None:
            raise ValueError("Config can't be None to execute a pipeline")

        input_nodes = self.input_loader.load(self.session)

        for step in self.run.steps:
            if is_debug_enabled():
                print(step)

            executor = step.get_step_config().get_executor(self.session, self.run, step)
            input_nodes = executor.execute_and_update_step(input_nodes, [], False)

        self.output_saver.save(input_nodes)

        self.run.update(self.session, RunStatus.FINISHED)
        CONSOLE.print(f"[green]Run {self.run.id} finished successfully!")


    @handle_run_errors
    @handle_stop_option
    def execute_from_last_failed_step(self):
        from synda.config import Config
        CONSOLE.print("[blue]Retrying last failed run")

        last_failed_step = Step.get_last_failed(self.session)

        if last_failed_step is None:
            raise Exception("Can't find any failed step.")

        self.run, input_nodes, remaining_steps = Run.restart_from_step(session=self.session, step=last_failed_step)
        self.config = Config.model_validate(self.run.config)
        self.output_saver = self.config.output.get_saver()
        restarted = True
        for step_ in remaining_steps:
            if is_debug_enabled():
                print(step_)

            executor = step_.get_step_config().get_executor(
                self.session, self.run, step_
            )
            if restarted:
                input_nodes = [node[0] for node in input_nodes if node[1] == "not_treated"]
                already_treated = [node[0] for node in input_nodes if node[1] == "treated"]
            else:
                already_treated = []
            input_nodes = executor.execute_and_update_step(input_nodes, already_treated, restarted)
            restarted = False

        self.output_saver.save(input_nodes)

        self.run.update(self.session, RunStatus.FINISHED)
        CONSOLE.print(f"[green]Run {self.run.id} finished successfully!")


    @handle_run_errors
    @handle_stop_option
    def resume(self, run_id: int):
        from synda.config import Config
        CONSOLE.print(f"[blue]Resuming run {run_id}")

        resumed_step = Step.get_step_to_resume(session=self.session, run_id=run_id)

        self.run, input_nodes, remaining_steps = Run.restart_from_step(session=self.session, step=resumed_step)
        self.config = Config.model_validate(self.run.config)
        self.output_saver = self.config.output.get_saver()
        restarted = True
        for step_ in remaining_steps:
            if is_debug_enabled():
                print(step_)

            executor = step_.get_step_config().get_executor(
                self.session, self.run, step_
            )
            if restarted:
                already_treated = [node[0] for node in input_nodes if node[1] == "treated"]
                input_nodes = [node[0] for node in input_nodes if node[1] == "not_treated"]
            else:
                already_treated = []
            input_nodes = executor.execute_and_update_step(input_nodes, already_treated, restarted)
            restarted = False

        self.output_saver.save(input_nodes)

        self.run.update(self.session, RunStatus.FINISHED)
        CONSOLE.print(f"[green]Run {self.run.id} finished successfully!")
