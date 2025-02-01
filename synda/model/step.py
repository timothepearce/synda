from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlmodel import Column, SQLModel, Field, Relationship, JSON, Session

from synda.database import engine
from synda.model.step_node import StepNode
from synda.model.node import Node

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

    def set_status(self, session: Session, status: str) -> "Step":
        self.status = status
        session.add(self)
        session.commit()
        session.refresh(self)

        return self

    def set_running(self, session: Session, input_nodes: list[Node]) -> "Step":
        self.status = StepStatus.RUNNING
        self.run_at = datetime.now()

        for node in input_nodes:
            if node.id is None:
                session.add(node)
        session.flush()

        for node in input_nodes:
            step_node = StepNode(
                step_id=self.id, node_id=node.id, relationship_type="input"
            )
            session.add(step_node)

        session.add(self)
        session.commit()
        session.refresh(self)

        return self

    def set_completed(self, session: Session, output_nodes: list[Node]) -> "Step":
        self.status = StepStatus.COMPLETED

        for node in output_nodes:
            if node.id is None:
                session.add(node)
        session.flush()

        for node in output_nodes:
            step_node = StepNode(
                step_id=self.id, node_id=node.id, relationship_type="output"
            )
            session.add(step_node)

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
            case "clean":
                from synda.config.clean import Deduplicate

                return Deduplicate.model_validate(self.step_config)
            case _:
                raise ValueError(f"Unknown step type: {self.step_type}")

    def _define_step_name(self, **data):
        if "step_name" in data and data["step_name"]:
            self.step_name = data["step_name"]
        else:
            self.step_name = f"{self.step_type}_{self.step_method}"
