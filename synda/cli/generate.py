from pathlib import Path
import typer

from synda.config import Config
from synda.pipeline import Pipeline


def generate_command(
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
