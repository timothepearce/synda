from pydantic import BaseModel

from nebula.config import Source


class Config(BaseModel):
    source: Source
