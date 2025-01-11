from typing import Literal

from pydantic import BaseModel


class Generation(BaseModel):
    type: Literal["generation"]
