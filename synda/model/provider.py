from sqlmodel import SQLModel, Field


class Provider(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    token: str | None = Field(default=None, unique=True)
