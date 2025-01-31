from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field, TypeAdapter
from sqlmodel import Session

from synda.config.step import Step
from synda.model.step import Step as StepModel
from synda.pipeline.executor import Executor

class DeduplicateParametersTFIDF(BaseModel):
    strategy: Literal["exact", "fuzzy"] = Field(
        default="exact", description="Strategy for removing duplicates"
    )
    similarity_threshold: Optional[float] = Field(
        default=0.9, description="Threshold for similarity"
    )
    keep: Literal["first", "last"] = Field(default="first", description="Keep the first or last duplicate")


class DeduplicateTFIDF(Step):
    type: str = "clean"
    method: Literal["deduplicate-td-idf"]
    parameters: DeduplicateParametersTFIDF

    def get_executor(self, session: Session, step_model: StepModel) -> Executor:
        if self.method == "deduplicate-td-idf":
            from synda.pipeline.clean import DeduplicateTFIDF

            return DeduplicateTFIDF(session, step_model)

Deduplicate = Annotated[DeduplicateTFIDF, Field(discriminator="method")]

deduplicate_adapter = TypeAdapter(Deduplicate)