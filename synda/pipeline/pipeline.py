from functools import wraps
from typing import TYPE_CHECKING
from sqlmodel import Session

from synda.database import engine
from synda.model.run import Run, RunStatus
from synda.model.step import Step
from synda.utils.env import is_debug_enabled

if TYPE_CHECKING:
    from synda.config import Config


class Pipeline:
    def __init__(self, config: "Config"):
        self.config = config
        self.session = Session(engine)
        self.input_loader = config.input.get_loader()
        self.output_saver = config.output.get_saver()
        self.pipeline = config.pipeline
        self.run = None

    @staticmethod
    def handle_run_errors(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                result = func(self, *args, **kwargs)
                self.run.update(self.session, RunStatus.FINISHED)
                return result
            except Exception as e:
                if self.run is not None:
                    self.run.update(self.session, RunStatus.ERRORED)
                raise e

        return wrapper

    @handle_run_errors
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

    @handle_run_errors
    def execute_from_last_failed_step(self):
        last_failed_step = Step.get_last_failed(self.session)

        if last_failed_step is None:
            raise Exception("Can't find any failed step.")

        self.run, input_nodes, remaining_steps = Run.restart_from_step(
            self.session, self.config, last_failed_step
        )

        for step in remaining_steps:
            if is_debug_enabled():
                print(step)

            executor = step.get_step_config().get_executor(self.session, self.run, step)
            input_nodes = executor.execute_and_update_step(input_nodes, restarted=True)

        self.output_saver.save(input_nodes)

        self.run.update(self.session, RunStatus.FINISHED)
