from typing import Literal

from pydantic import BaseModel

from nebula.config.input.csv import CSVInputProperties
from nebula.config.input.database import DatabaseInputProperties


class Input(BaseModel):
    type: Literal["csv"]
    properties: CSVInputProperties  # | DatabaseSourceProperties
