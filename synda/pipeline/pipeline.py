from typing import TYPE_CHECKING

from synda.model.run import Run, RunStatus
from synda.pipeline.pipeline_context import PipelineContext
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
        self.pipeline_context: PipelineContext = PipelineContext()

    def execute(self):
        try:
            self.input_loader.load(self.pipeline_context)

            for step in self.run.steps:
                print(step)
                if is_debug_enabled():
                    print(step.get_step_config())

                executor = step.get_step_config().get_executor(step)
                executor.execute_and_update_step(self.pipeline_context)

            self.output_saver.save(self.pipeline_context)

            self.run.update(status=RunStatus.FINISHED)
        except Exception as e:
            self.run.update(status=RunStatus.ERRORED)
            raise e
