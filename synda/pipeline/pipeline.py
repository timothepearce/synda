from typing import TYPE_CHECKING

from synda.model.run import Run, RunStatus
from synda.utils import is_debug_enabled

if TYPE_CHECKING:
    from synda.config import Config


class Pipeline:
    def __init__(self, config: "Config"):
        self.config = config
        self.run = Run.create_with_steps(config)
        self.input_loader = config.input.get_loader()
        self.output_saver = config.output.get_saver()
        self.pipeline = config.pipeline

    def execute(self):
        try:
            input_data = self.input_loader.load()

            for step in self.run.steps:
                if is_debug_enabled():
                    print(step)

                executor = step.get_step_config().get_executor(step)
                input_data = executor.execute_and_update_step(input_data)

            self.output_saver.save(input_data)

            self.run.update(status=RunStatus.FINISHED)
        except Exception as e:
            self.run.update(status=RunStatus.ERRORED)
            raise e
