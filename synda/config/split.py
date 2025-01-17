from typing import Literal

from pydantic import BaseModel, Field

from synda.config.step import Step
from synda.pipeline.executor import Executor


class SplitParameters(BaseModel):
    size: int = Field(
        default=500,
        gt=0,
        lt=10000,
        description="Size of each chunk in characters"
    )


class Split(Step):
    type: str = "split"
    method: Literal["chunk"]
    parameters: SplitParameters

    def get_executor(self) -> Executor:
        if self.method == "chunk":
            from synda.pipeline.split import Chunk
            return Chunk(self)
