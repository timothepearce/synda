from enum import Enum
from typing import Literal, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from synda.config.step import Step
    from synda.model.node import Node


class StepNodeRelationshipType(Enum):
    INPUT = "input"
    OUTPUT = "output"


class StepNode(SQLModel, table=True):
    __tablename__ = "step_node"

    step_id: int = Field(foreign_key="step.id", primary_key=True)
    node_id: int = Field(foreign_key="node.id", primary_key=True)
    relationship_type: StepNodeRelationshipType = Field(index=True)

    step: "Step" = Relationship(back_populates="step_node_links")
    node: "Node" = Relationship(back_populates="step_node_links")
