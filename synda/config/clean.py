from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field, TypeAdapter
from sqlmodel import Session

from synda.config.step import Step
from synda.model.run import Run
from synda.model.step import Step as StepModel
from synda.pipeline.executor import Executor


class DeduplicateParametersTFIDF(BaseModel):
    strategy: Literal["exact", "fuzzy"] = Field(
        default="exact", description="Strategy for removing duplicates"
    )
    similarity_threshold: Optional[float] = Field(
        default=0.9, description="Threshold for similarity"
    )
    keep: Literal["first", "last"] = Field(
        default="first", description="Keep the first or last duplicate"
    )

class DeduplicateParametersEmbed(BaseModel):
    provider: str = Field(description="Provider name (e.g. mistral, openai)")
    model: str = Field(description="Embedding model name")
    similarity_threshold: float = Field(default=0.7, description="Threshold for similarity (distance)")


class DeduplicateTFIDF(Step):
    type: str = "clean"
    method: Literal["deduplicate-tf-idf"]
    parameters: DeduplicateParametersTFIDF

    def get_executor(
        self, session: Session, run: Run, step_model: StepModel
    ) -> Executor:
        from synda.pipeline.clean import DeduplicateTFIDF

        return DeduplicateTFIDF(session, run, step_model)


class DeduplicateEmbed(Step):
    type: str = "clean"
    method: Literal["deduplicate-embed"]
    parameters: DeduplicateParametersEmbed

    def get_executor(
        self, session: Session, run: Run, step_model: StepModel
    ) -> Executor:
        from synda.pipeline.clean import DeduplicateEmbed

        return DeduplicateEmbed(session, run, step_model)

Clean = Annotated[DeduplicateTFIDF | DeduplicateEmbed, Field(discriminator="method")]

deduplicate_adapter = TypeAdapter(Clean)
