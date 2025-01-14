from typing import Literal

from pydantic import BaseModel

from nebula.config.source.csv import CSVSourceProperties
from nebula.config.source.database import DatabaseSourceProperties


class Source(BaseModel):
    type: Literal["csv"]
    properties: CSVSourceProperties  # | DatabaseSourceProperties
