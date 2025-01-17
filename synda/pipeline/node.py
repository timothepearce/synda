from __future__ import annotations
from pydantic import BaseModel


class Node(BaseModel):
    value: str
    from_node: Node | None
