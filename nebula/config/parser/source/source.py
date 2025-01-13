from typing import Literal

from pydantic import BaseModel

from nebula.config.parser.source.csv import CSVSourceProperties
from nebula.config.parser.source.database import DatabaseSourceProperties


class Source(BaseModel):
    type: Literal["csv"]
    properties: CSVSourceProperties  # | DatabaseSourceProperties
