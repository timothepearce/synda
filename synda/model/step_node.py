from typing import Literal, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from synda.config.step import Step
    from synda.model.node import Node


class StepNode(SQLModel, table=True):
    __tablename__ = "step_node"

    step_id: int = Field(foreign_key="step.id", primary_key=True)
    node_id: int = Field(foreign_key="node.id", primary_key=True)
    relationship_type: str = Field(
        index=True
    )  # @todo add constraint for "input" or "output" only

    step: "Step" = Relationship(back_populates="step_node_links")
    node: "Node" = Relationship(back_populates="step_node_links")
