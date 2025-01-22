from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlmodel import Column, SQLModel, Field, Relationship, JSON

from synda.pipeline.node import Node

if TYPE_CHECKING:
    from synda.config.step import Step as StepConfig
    from synda.model.run import Run


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERRORED = "errored"


class Step(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="run.id")
    position: int = Field()
    step_name: str = Field(index=True)
    step_method: str = Field()
    step_config: "StepConfig" = Field(
        default_factory=dict,
        sa_column=Column(JSON)
    )
    status: StepStatus = Field(default=StepStatus.PENDING)
    input_data: list[Node] | None = Field(
        default=None,
        sa_column=Column(JSON)
    )
    output_data: list[Node] = Field(
        default_factory=list,
        sa_column=Column(JSON)
    )
    run_at: datetime | None = Field()

    run: "Run" = Relationship(back_populates="steps")

    def get_step_config(self) -> "StepConfig":
        # @todo reimplement with dynamic concrete class resolution and instanciation
        if self.step_name == "split":
            from synda.config.split import Split
            return Split.model_validate(self.step_config)
        elif self.step_name == "generation":
            from synda.config.generation import Generation
            return Generation.model_validate(self.step_config)
        elif self.step_name == "ablation":
            from synda.config.ablation import Ablation
            return Ablation.model_validate(self.step_config)
