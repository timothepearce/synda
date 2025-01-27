from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlmodel import Column, SQLModel, Field, Relationship, JSON, Session

from synda.database import engine
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

    def update_execution(self, status: StepStatus, input_data: list[Node] | None = None, output_data: list[Node] | None = None) -> "Step":
        with Session(engine) as session:
            self.status = status

            if input_data is not None:
                self.input_data = [node.model_dump() for node in input_data]

            if output_data is not None:
                self.output_data = [node.model_dump() for node in output_data]

            session.add(self)
            session.commit()
            session.refresh(self)

            return self

    def get_step_config(self) -> "StepConfig":
        # @todo reimplement with a dynamic class resolution
        if self.step_name == "split":
            from synda.config.split import split_adapter
            return split_adapter.validate_python(self.step_config)
        elif self.step_name == "generation":
            from synda.config.generation import Generation
            return Generation.model_validate(self.step_config)
        elif self.step_name == "ablation":
            from synda.config.ablation import Ablation
            return Ablation.model_validate(self.step_config)
