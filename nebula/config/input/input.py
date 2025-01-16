from typing import Literal

from pydantic import BaseModel

from nebula.config.input.csv import CSVInputProperties
from nebula.config.input.database import DatabaseInputProperties

from nebula.pipeline.input import InputLoader


class Input(BaseModel):
    type: Literal["csv"]
    properties: CSVInputProperties  # | DatabaseSourceProperties

    def get_loader(self) -> InputLoader:
        if self.type == "csv":
            from nebula.pipeline.input.csv_input_loader import CSVInputLoader
            return CSVInputLoader(self)
