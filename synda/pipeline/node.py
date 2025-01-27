from __future__ import annotations
from uuid import uuid4

from pydantic import BaseModel, Field


class Node(BaseModel):
    uuid: str = Field(default_factory=lambda: str(uuid4()))
    parent_node_uuid: str | None = None
    ablated: bool = False
    value: str

    def is_ablated_text(self) -> str:
        return "yes" if self.ablated else "no"
