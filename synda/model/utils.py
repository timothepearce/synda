import re

from sqlalchemy.ext.declarative import declared_attr
from sqlmodel import SQLModel as _SQLModel


def snake_case(name: str) -> str:
    name = name.strip().replace("-", "_").replace(" ", "_")
    name = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name)
    name = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", "_", name)

    return name.lower()


class SQLModel(_SQLModel):
    """
    SQLModel with snake_case table names
    """

    @declared_attr  # type: ignore
    def __tablename__(cls) -> str:  # type: ignore
        return snake_case(cls.__name__)
