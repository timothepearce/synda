from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlmodel import Column, SQLModel, Field, Relationship, JSON, Session

from synda.database import engine
from synda.model.step_node import StepNode
from synda.model.node import Node
from synda.pipeline.node import Node as NodePipeline

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
    step_type: str = Field(index=True)
    step_method: str = Field()
    step_name: str = Field(index=True)
    step_config: "StepConfig" = Field(default_factory=dict, sa_column=Column(JSON))
    status: StepStatus = Field(default=StepStatus.PENDING)
    input_data: list[NodePipeline] | None = Field(default=None, sa_column=Column(JSON))
    output_data: list[NodePipeline] = Field(
        default_factory=list, sa_column=Column(JSON)
    )
    run_at: datetime | None = Field()

    run: "Run" = Relationship(back_populates="steps")

    step_node_links: list["StepNode"] = Relationship(
        back_populates="step",
        sa_relationship_kwargs={"overlaps": "input_step,output_step"},
    )

    input_nodes: list[Node] = Relationship(
        back_populates="input_step",
        link_model=StepNode,
        sa_relationship_kwargs={
            "primaryjoin": "and_(Step.id == StepNode.step_id, StepNode.relationship_type == 'input')",
            "secondaryjoin": "Node.id == StepNode.node_id",
            "secondary": "step_node",
            "overlaps": "output_step,step,step_node_links,node",
        },
    )

    output_nodes: list[Node] = Relationship(
        back_populates="output_step",
        link_model=StepNode,
        sa_relationship_kwargs={
            "primaryjoin": "and_(Step.id == StepNode.step_id, StepNode.relationship_type == 'output')",
            "secondaryjoin": "Node.id == StepNode.node_id",
            "secondary": "step_node",
            "overlaps": "input_nodes,input_step,step,step_node_links,node",
        },
    )

    def __init__(self, **data):
        super().__init__(**data)
        self._define_step_name(**data)

    def update_execution(
        self,
        status: StepStatus,
        input_data: list[NodePipeline] | None = None,
        output_data: list[NodePipeline] | None = None,
    ) -> "Step":
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
        match self.step_type:
            case "split":
                from synda.config.split import split_adapter

                return split_adapter.validate_python(self.step_config)
            case "generation":
                from synda.config.generation import Generation

                return Generation.model_validate(self.step_config)
            case "ablation":
                from synda.config.ablation import Ablation

                return Ablation.model_validate(self.step_config)
            case _:
                raise ValueError(f"Unknown step type: {self.step_type}")

    def _define_step_name(self, **data):
        if "step_name" in data and data["step_name"]:
            self.step_name = data["step_name"]
        else:
            self.step_name = f"{self.step_type}_{self.step_method}"
