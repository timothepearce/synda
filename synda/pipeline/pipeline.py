from typing import TYPE_CHECKING
from sqlmodel import Session

from synda.database import engine
from synda.model.run import Run, RunStatus
from synda.utils import is_debug_enabled

if TYPE_CHECKING:
    from synda.config import Config


class Pipeline:
    def __init__(self, config: "Config"):
        self.config = config
        self.session = Session(engine)
        self.input_loader = config.input.get_loader()
        self.output_saver = config.output.get_saver()
        self.pipeline = config.pipeline
        self.run = Run.create_with_steps(self.session, config)

    def execute(self):
        try:
            input_nodes = self.input_loader.load(self.session)

            for step in self.run.steps:
                if is_debug_enabled():
                    print(step)

                executor = step.get_step_config().get_executor(self.session, step)
                input_nodes = executor.execute_and_update_step(input_nodes)

            self.output_saver.save(input_nodes)

            self.run.update(self.session, RunStatus.FINISHED)
        except Exception as e:
            self.run.update(self.session, RunStatus.ERRORED)
            raise e
