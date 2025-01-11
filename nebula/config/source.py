from typing import Literal

from pydantic import BaseModel


class SourceProperties(BaseModel):
    path: str
    target_column: str


class Source(BaseModel):
    type: Literal["csv"]
    properties: SourceProperties
