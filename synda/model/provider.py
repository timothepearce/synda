import typer
from sqlmodel import SQLModel, Session, Field, select

from synda.database import engine


class Provider(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    api_key: str | None = Field(default=None, unique=True)

    @staticmethod
    def get(name: str) -> "Provider":
        with Session(engine) as session:
            provider = session.exec(
                select(Provider).where(Provider.name == name)
            ).first()

            if not provider:
                typer.secho(
                    f"Provider {name} not found in database. "
                    "Please add it using 'synda provider add <name> --api-key <key>'",
                    fg=typer.colors.RED
                )
                raise typer.Exit(1)

            return provider
