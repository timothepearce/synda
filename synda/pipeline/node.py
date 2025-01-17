from __future__ import annotations
from pydantic import BaseModel


class Node(BaseModel):
    value: str
    ablated: bool = True
    from_node: Node | None

    def is_ablated_text(self) -> str:
        return "yes" if self.ablated else "no"
