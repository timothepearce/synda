from enum import Enum
from typing import Optional

import typer
from sqlmodel import Session, select

from synda.database import engine
from synda.model.provider import Provider


class ProviderAction(str, Enum):
    ADD = "add"
    DELETE = "delete"
    UPDATE = "update"


def get_provider_by_name(session: Session, name: str) -> Optional[Provider]:
    """Récupère un provider par son nom."""
    statement = select(Provider).where(Provider.name == name)
    return session.exec(statement).first()


def add_provider(session: Session, name: str, api_key: str | None) -> None:
    existing = get_provider_by_name(session, name)
    if existing:
        typer.secho(f"Provider {name} already exists", fg=typer.colors.YELLOW)
        raise typer.Exit(1)

    provider = Provider(name=name, token=api_key)
    session.add(provider)
    session.commit()
    typer.secho(f"Successfully added provider: {name}", fg=typer.colors.GREEN)


def delete_provider(session: Session, name: str) -> None:
    provider = get_provider_by_name(session, name)
    if not provider:
        typer.secho(f"Provider {name} not found", fg=typer.colors.RED)
        raise typer.Exit(1)

    session.delete(provider)
    session.commit()
    typer.secho(f"Successfully deleted provider: {name}", fg=typer.colors.GREEN)


def update_provider(session: Session, name: str, api_key: str) -> None:
    if not api_key:
        typer.secho("API key is required for updating a provider", fg=typer.colors.RED)
        raise typer.Exit(1)

    provider = get_provider_by_name(session, name)
    if not provider:
        typer.secho(f"Provider {name} not found", fg=typer.colors.RED)
        raise typer.Exit(1)

    provider.token = api_key
    session.add(provider)
    session.commit()
    typer.secho(f"Successfully updated provider: {name}", fg=typer.colors.GREEN)


def provider_command(
        action: ProviderAction = typer.Argument(
            ...,
            help="Action to perform: add, delete, or update"
        ),
        model_provider: str = typer.Argument(
            ...,
            help="Model provider name"
        ),
        api_key: str = typer.Option(
            None,
            "--api-key",
            "-k",
            help="API key for model provider",
        )
):
    with Session(engine) as session:
        action_handlers = {
            ProviderAction.ADD: lambda: add_provider(session, model_provider, api_key),
            ProviderAction.DELETE: lambda: delete_provider(session, model_provider),
            ProviderAction.UPDATE: lambda: update_provider(session, model_provider, api_key)
        }

        action_handlers[action]()
