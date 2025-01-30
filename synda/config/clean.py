from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field, TypeAdapter
from sqlmodel import Session

from synda.config.step import Step
from synda.model.step import Step as StepModel
from synda.pipeline.executor import Executor

class RemoveDuplicatesParameters(BaseModel):
    strategy: Literal["exact", "fuzzy"] = Field(
        default="exact", description="Strategy for removing duplicates"
    )
    similarity_threshold: Optional[float] = Field(
        default=0.9, description="Threshold for similarity"
    )
    keep: Literal["first", "last"] = Field(default="first", description="Keep the first or last duplicate")


class RemoveDuplicates(Step):
    type: str = "clean"
    method: Literal["remove_duplicates"]
    parameters: RemoveDuplicatesParameters

    def get_executor(self, session: Session, step_model: StepModel) -> Executor:
        if self.method == "remove_duplicates":
            from synda.pipeline.clean import RemoveDuplicates

            return RemoveDuplicates(session, step_model)

RemoveDuplicates = Annotated[RemoveDuplicates, Field(discriminator="method")]

remove_duplicates_adapter = TypeAdapter(RemoveDuplicates)