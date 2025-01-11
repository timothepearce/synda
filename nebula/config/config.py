from pydantic import BaseModel

from nebula.config.source import Source


class Config(BaseModel):
    source: Source
