from enum import Enum
from typing import TYPE_CHECKING, Union, Any
from sqlmodel import SQLModel, Field, Relationship, Column, JSON, Session, select
from sqlalchemy import and_

from synda.model.step_node import StepNode, StepNodeRelationshipType

if TYPE_CHECKING:
    from synda.model.step import Step


class NodeStatus(Enum):
    PENDING = "pending"
    PROCESSED = "processed"


class Node(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    parent_node_id: int | None = None
    ablated: bool = False
    value: str
    ancestors: dict = Field(default_factory=dict, sa_column=Column(JSON))
    status: NodeStatus = Field(default=NodeStatus.PENDING)
    node_metadata: list[dict[str, Any]] = Field(
        default_factory=list, sa_column=Column(JSON)
    )

    step_node_links: list["StepNode"] = Relationship(back_populates="node")

    input_step: list["Step"] = Relationship(
        back_populates="input_nodes",
        link_model=StepNode,
        sa_relationship_kwargs={
            "primaryjoin": f"and_(Node.id == StepNode.node_id, StepNode.relationship_type == '{StepNodeRelationshipType.INPUT.value}')",  # noqa
            "secondaryjoin": "Step.id == StepNode.step_id",
            "secondary": "step_node",
            "overlaps": "step,node,step_node_links",
        },
    )

    output_step: list["Step"] = Relationship(
        back_populates="output_nodes",
        link_model=StepNode,
        sa_relationship_kwargs={
            "primaryjoin": f"and_(Node.id == StepNode.node_id, StepNode.relationship_type == '{StepNodeRelationshipType.OUTPUT.value}')",  # noqa
            "secondaryjoin": "Step.id == StepNode.step_id",
            "secondary": "step_node",
            "overlaps": "input_step,node,step_node_links,step",
        },
    )

    @classmethod
    def get(
        cls, session: Session, node_ids: Union[int, list[int]]
    ) -> Union["Node", list["Node"]]:
        if isinstance(node_ids, int):
            node_ids = [node_ids]
            single_result = True
        else:
            single_result = False

        query = select(cls).where(cls.id.in_(node_ids))
        results = session.exec(query).all()

        return results[0] if single_result and results else results

    @staticmethod
    def get_input_nodes_from_step(session: Session, step: "Step") -> list["Node"]:
        return session.exec(
            select(Node)
            .join(StepNode, Node.id == StepNode.node_id)
            .where(
                and_(
                    StepNode.step_id == step.id,
                    StepNode.relationship_type == StepNodeRelationshipType.INPUT.value,
                )
            )
        ).fetchall()

    def is_ablated_text(self) -> str:
        return "yes" if self.ablated else "no"

    def set_processed(self, session: Session):
        self.status = NodeStatus.PROCESSED
        session.add(self)
        session.commit()
        session.refresh(self)
