from pathlib import Path

import typer
from dotenv import load_dotenv

from synda.config import Config
from synda.database import init_db
from synda.pipeline import Pipeline


app = typer.Typer(
    name="synda",
    help="A synthetic data generator pipeline CLI.",
    add_completion=False,
)


@app.command("provider")
def provider(
    action: str = typer.Argument(
        help="Add or delete"
    ),
    model_provider: str = typer.Argument(
        ...,
        help="Model provider name"
    ),
    api_key: str = typer.Option(
        ...,
        help="API key for model provider",
    )
):
    """Add or delete a model provider."""
    print(f"@todo: {action} the {model_provider} with key: {api_key}.")


@app.command("generate")
def generate(
    config_file: Path = typer.Argument(
        ...,
        help="Path to YAML configuration file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
):
    """Run a pipeline with provided configuration."""
    config = Config.load_config(config_file)
    pipeline = Pipeline(config)
    pipeline.execute()


def main():
    load_dotenv()
    init_db()
    app()


if __name__ == "__main__":
    main()
