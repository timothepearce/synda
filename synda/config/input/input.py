from typing import Literal

from pydantic import BaseModel

from synda.config.input.csv import CSVInputProperties
from synda.config.input.database import DatabaseInputProperties

from synda.pipeline.input import InputLoader


class Input(BaseModel):
    type: Literal["csv"]
    properties: CSVInputProperties  # | DatabaseSourceProperties

    def get_loader(self) -> InputLoader:
        if self.type == "csv":
            from synda.pipeline.input.csv_input_loader import CSVInputLoader

            return CSVInputLoader(self)
