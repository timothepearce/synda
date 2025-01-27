from enum import Enum

import typer
from sqlalchemy.exc import IntegrityError, NoResultFound

from synda.model.provider import Provider


class ProviderAction(str, Enum):
    ADD = "add"
    DELETE = "delete"
    UPDATE = "update"


def add_provider(name: str, api_key: str | None) -> None:
    try:
        Provider.create(name=name, api_key=api_key)
        typer.secho(f"Successfully added provider: {name}", fg=typer.colors.GREEN)
    except IntegrityError as e:
        typer.secho(f"Provider {name} already exists", fg=typer.colors.YELLOW)
        raise typer.Exit(1)


def delete_provider(name: str) -> None:
    try:
        provider = Provider.get(name)
        provider.delete()
        typer.secho(f"Successfully deleted provider: {name}", fg=typer.colors.GREEN)
    except NoResultFound as e:
        typer.secho(
            f"Provider {name} not found in database. "
            "Please add it using 'synda provider add <name> --api-key <key>'",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)


def update_provider(name: str, api_key: str) -> None:
    if not api_key:
        typer.secho("API key is required for updating a provider", fg=typer.colors.RED)
        raise typer.Exit(1)

    try:
        provider = Provider.get(name)
        provider.update(api_key=api_key)
        typer.secho(f"Successfully updated provider: {name}", fg=typer.colors.GREEN)
    except NoResultFound as e:
        typer.secho(f"Provider {name} not found", fg=typer.colors.RED)
        raise typer.Exit(1)


def provider_command(
    action: ProviderAction = typer.Argument(
        ..., help="Action to perform: add, delete, or update"
    ),
    model_provider: str = typer.Argument(..., help="Model provider name"),
    api_key: str = typer.Option(
        None,
        "--api-key",
        "-k",
        help="API key for model provider",
    ),
):
    action_handlers = {
        ProviderAction.ADD: lambda: add_provider(model_provider, api_key),
        ProviderAction.DELETE: lambda: delete_provider(model_provider),
        ProviderAction.UPDATE: lambda: update_provider(model_provider, api_key),
    }

    action_handlers[action]()
