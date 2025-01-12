from abc import ABC, abstractmethod

from pydantic import BaseModel

from nebula.pipeline.pipeline_context import PipelineContext


class Step(BaseModel, ABC):
    type: str

    @abstractmethod
    def execute(self, pipeline_data: PipelineContext) -> PipelineContext:
        pass
