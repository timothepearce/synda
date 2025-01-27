from typing import TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

from synda.model.step_node import StepNode

if TYPE_CHECKING:
    from synda.model.step import Step


class Node(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    parent_node_id: int | None = None
    ablated: bool = False
    value: str

    step_node_links: list["StepNode"] = Relationship(back_populates="node")

    input_step: list["Step"] = Relationship(
        back_populates="input_nodes",
        link_model=StepNode,
        sa_relationship_kwargs={
            "primaryjoin": "and_(Node.id == StepNode.node_id, StepNode.relationship_type == 'input')",
            "secondaryjoin": "Step.id == StepNode.step_id",
            "secondary": "step_node",
            "overlaps": "step,node,step_node_links",
        },
    )

    output_step: list["Step"] = Relationship(
        back_populates="output_nodes",
        link_model=StepNode,
        sa_relationship_kwargs={
            "primaryjoin": "and_(Node.id == StepNode.node_id, StepNode.relationship_type == 'output')",
            "secondaryjoin": "Step.id == StepNode.step_id",
            "secondary": "step_node",
            "overlaps": "input_step,node,step_node_links,step",
        },
    )

    def is_ablated_text(self) -> str:
        return "yes" if self.ablated else "no"
