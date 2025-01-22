from abc import abstractmethod

from synda.model.step import Step
from synda.pipeline.pipeline_context import PipelineContext


class Executor:
    def __init__(self, step_model: Step):
        self.step_model = step_model
        self.config = step_model.get_step_config()

    @abstractmethod
    def execute(self, pipeline_context: PipelineContext):
        pass
