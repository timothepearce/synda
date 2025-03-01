from pathlib import Path
import typer
from typing import Optional

from synda.config import Config
from synda.pipeline import Pipeline


def generate_command(
    config_file: Path = typer.Argument(
        default=None,
        help="Path to YAML configuration file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    retry: bool = typer.Option(
        False, "--retry", "-r", help="Run the pipeline from last failed step"
    ),
    run_id: Optional[int] = typer.Option(
        None, "--resume", "-re", help="Resume the pipeline from a given run id"
    ),
):
    """Run a pipeline with provided configuration."""
    if retry:
        Pipeline().retry()
    elif run_id is not None:
        Pipeline().resume(run_id=run_id)
    else:
        config = Config.load_config(config_file)
        pipeline = Pipeline(config)
        pipeline.execute()
