from pydantic import BaseModel


class Node(BaseModel):
    value: str
    history: list["Node"] | None
