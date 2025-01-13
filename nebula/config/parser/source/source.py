from typing import Literal

from pydantic import BaseModel

from nebula.config.parser.source.csv import CSVSourceProperties


class DatabaseSourceProperties(BaseModel):
    pass


class Source(BaseModel):
    type: Literal["csv"]
    properties: CSVSourceProperties  # | DatabaseSourceProperties -> to add another source
