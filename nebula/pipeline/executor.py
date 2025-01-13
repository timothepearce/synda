from abc import abstractmethod

from nebula.config.parser import Step
from nebula.pipeline.pipeline_context import PipelineContext


class Executor:
    def __init__(self, config: Step):
        self.config = config

    @abstractmethod
    def execute(self, pipeline_context: PipelineContext):
        pass
