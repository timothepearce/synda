from typing import Literal

from pydantic import BaseModel

from nebula.config.output.csv import CSVOutputProperties


class Output(BaseModel):
    type: Literal["csv"]
    properties: CSVOutputProperties
