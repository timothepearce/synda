from abc import abstractmethod

from synda.pipeline.pipeline_context import PipelineContext


class InputLoader:
    @abstractmethod
    def load(self, pipeline_context: PipelineContext) -> None:
        pass
