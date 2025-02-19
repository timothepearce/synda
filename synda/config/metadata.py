from typing import Annotated, Literal

from pydantic import BaseModel, Field, TypeAdapter
from sqlmodel import Session

from synda.config.step import Step
from synda.model.run import Run
from synda.model.step import Step as StepModel
from synda.pipeline.executor import Executor


class WordPositionParameters(BaseModel):
    matches: dict[str, str] = Field(
        description="A dictionary with 'key' = LABEl and 'value' = string to match"
    )


class WordPosition(Step):
    type: str = "metadata"
    method: Literal["word-position"]
    parameters: WordPositionParameters

    def get_executor(
        self, session: Session, run: Run, step_model: StepModel
    ) -> Executor:
        from synda.pipeline.metadata import WordPosition

        return WordPosition(session, run, step_model)


Metadata = Annotated[WordPosition, Field(discriminator="method")]

metadata_adapter = TypeAdapter(Metadata)
