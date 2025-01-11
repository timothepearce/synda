from typing import Literal

from pydantic import BaseModel


class Ablation(BaseModel):
    type: Literal["ablation"]
