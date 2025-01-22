from abc import abstractmethod

from synda.model.step import Step, StepStatus
from synda.pipeline.pipeline_context import PipelineContext


class Executor:
    def __init__(self, step_model: Step):
        self.step_model = step_model
        self.config = step_model.get_step_config()

    def execute_and_update_step(self, pipeline_context: PipelineContext):
        try:
            self.step_model.update_status(StepStatus.RUNNING)
            self.execute(pipeline_context)
            self.step_model.update_status(StepStatus.COMPLETED)
        except Exception as e:
            self.step_model.update_status(StepStatus.ERRORED)
            raise e

    @abstractmethod
    def execute(self, pipeline_context: PipelineContext):
        pass
