from functools import wraps
from typing import TYPE_CHECKING, Optional

from rich.console import Console
from rich.markup import escape
from sqlmodel import Session

from synda.model.node import Node, NodeStatus
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

                    user_input = (
                        CONSOLE.input(f"[red]{escaped_prompt}[/]").strip().lower()
                    )

                    if user_input == "y":
                        self.run.update(self.session, RunStatus.STOPPED)
                        CONSOLE.print(
                            f"[blue]Run with id {self.run.id} is stopped.\nTo resume the run, use:"
                        )
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
            self._log_debug_info(step)
            executor = step.get_step_config().get_executor(self.session, self.run, step)
            input_nodes = executor.execute_and_update_step(input_nodes, [], False)

        self._finalize_run(input_nodes)

    @handle_run_errors
    @handle_stop_option
    def retry(self):
        CONSOLE.print("[blue]Retrying last failed run")
        last_failed_step = Step.get_last_failed(self.session)

        if last_failed_step is None:
            raise Exception("Can't find any failed step.")

        self._restart_from_step(last_failed_step)

    @handle_run_errors
    @handle_stop_option
    def resume(self, run_id: int):
        CONSOLE.print(f"[blue]Resuming run {run_id}")
        resumed_step = Step.get_step_to_resume(session=self.session, run_id=run_id)
        self._restart_from_step(resumed_step)

    def _restart_from_step(self, step: Step):
        from synda.config import Config

        self.run, input_nodes, remaining_steps = Run.restart_from_step(
            session=self.session, step=step
        )
        self.config = Config.model_validate(self.run.config)
        self.output_saver = self.config.output.get_saver()

        self._execute_remaining_steps(input_nodes, remaining_steps)

        self._finalize_run(input_nodes)

    def _execute_remaining_steps(self, input_nodes, remaining_steps):
        is_first_remaining_step = True

        for current_step in remaining_steps:
            self._log_debug_info(current_step)
            executor = current_step.get_step_config().get_executor(
                self.session, self.run, current_step
            )

            nodes_to_process, processed_nodes = self._prepare_nodes(
                input_nodes, is_first_remaining_step
            )

            input_nodes = executor.execute_and_update_step(
                nodes_to_process, processed_nodes, is_first_remaining_step
            )
            is_first_remaining_step = False

        return input_nodes

    @staticmethod
    def _prepare_nodes(input_nodes, is_first_step):
        if not is_first_step:
            return input_nodes, []

        pending_nodes, processed_nodes = [], []

        for node in input_nodes:
            if node.status == NodeStatus.PENDING:
                pending_nodes.append(node)
            elif node.status == NodeStatus.PROCESSED:
                processed_nodes.append(node)

        return pending_nodes, processed_nodes

    @staticmethod
    def _log_debug_info(step):
        if is_debug_enabled():
            print(step)

    def _finalize_run(self, input_nodes: list[Node]):
        self.output_saver.save(input_nodes)
        self.run.update(self.session, RunStatus.FINISHED)
        CONSOLE.print(f"[green]Run {self.run.id} finished successfully!")
