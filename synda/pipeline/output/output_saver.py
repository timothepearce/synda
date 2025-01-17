from abc import abstractmethod

from synda.pipeline.pipeline_context import PipelineContext


class OutputSaver:
    @abstractmethod
    def save(self, pipeline_context: PipelineContext):
        pass
