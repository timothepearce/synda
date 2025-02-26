from functools import wraps
from typing import TYPE_CHECKING

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

def handle_run_errors(func):
    """Decorator to handle run errors gracefully."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if hasattr(args[0], 'run') and args[0].run is not None:
                args[0].run.update(args[0].session, RunStatus.ERRORED)
            raise e
    return wrapper


def handle_stop_option(func):
    """Decorator to handle user interruption (Ctrl+C) during execution."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            self = args[0]  # Get the instance
            if hasattr(self, 'run') and self.run is not None:
                prompt = f"\nAre you sure you want to stop the run {self.run.id}? [y/N]: "
                escaped_prompt = escape(prompt)

                user_input = CONSOLE.input(f"[red]{escaped_prompt}[/]").strip().lower()

                if user_input == 'y':
                    self.run.update(self.session, RunStatus.STOPPED)
                    CONSOLE.print(f"[blue]Run with id {self.run.id} is stopped.\nTo resume the run, use:")
                    CONSOLE.print(f"[cyan]synda generate --resume {self.run.id}")
                    exit(0)
                else:
                    Pipeline.resume(run_id=self.run.id)
    return wrapper

class Pipeline:
    def __init__(self, config: "Config"):
        self.config = config
        self.session = Session(engine)
        self.input_loader = config.input.get_loader()
        self.output_saver = config.output.get_saver()
        self.pipeline = config.pipeline
        self.run = None

    @handle_run_errors
    @handle_stop_option
    def execute(self):
        self.run = Run.create_with_steps(self.session, self.config)
        input_nodes = self.input_loader.load(self.session)

        for step in self.run.steps:
            if is_debug_enabled():
                print(step)

            executor = step.get_step_config().get_executor(self.session, self.run, step)
            input_nodes = executor.execute_and_update_step(input_nodes)

        self.output_saver.save(input_nodes)

        self.run.update(self.session, RunStatus.FINISHED)
        CONSOLE.print(f"[green]Run {self.run.id} finished successfully!")

    @staticmethod
    @handle_run_errors
    def execute_from_last_failed_step():
        from synda.config import Config
        CONSOLE.print("[blue]Retrying last failed run")

        session = Session(engine)
        last_failed_step = Step.get_last_failed(session)

        if last_failed_step is None:
            raise Exception("Can't find any failed step.")

        run, input_nodes, remaining_steps = Run.restart_from_step(session=session, step=last_failed_step)
        config = Config.model_validate(run.config)
        output_saver = config.output.get_saver()
        for step in remaining_steps:
            if is_debug_enabled():
                print(step)

            executor = step.get_step_config().get_executor(session, run, step)
            input_nodes = executor.execute_and_update_step(input_nodes, restarted=True)

        output_saver.save(input_nodes)

        run.update(session, RunStatus.FINISHED)
        print(f"[green]Run {run.id} finished successfully!")


    @staticmethod
    @handle_run_errors
    def resume(run_id: int):
        from synda.config import Config
        CONSOLE.print(f"[blue]Resuming run {run_id}")

        session = Session(engine)
        resumed_step = Step.get_step_to_resume(session=session, run_id=run_id)

        run, input_nodes, remaining_steps = Run.restart_from_step(session=session, step=resumed_step)
        config = Config.model_validate(run.config)
        output_saver = config.output.get_saver()
        for step_ in remaining_steps:
            if is_debug_enabled():
                print(step_)

            executor = step_.get_step_config().get_executor(
                session, run, step_
            )
            input_nodes = executor.execute_and_update_step(input_nodes, restarted=True)

        output_saver.save(input_nodes)

        run.update(session, RunStatus.FINISHED)
        CONSOLE.print(f"[green]Run {run.id} finished successfully!")
