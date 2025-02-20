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
    retry: bool = typer.Option(
        False, "--retry", "-r", help="Run the pipeline from last failed step"
    ),
    resume: bool = typer.Option(
        False,
        "--resume",
        "-k",
        help="Resume the pipeline from a given run id"
    ),
    run_id: int = typer.Option(
        None,
        help="Run id to resume. Only use if --resume=True"
    )
):
    """Run a pipeline with provided configuration."""
    config = Config.load_config(config_file)
    pipeline = Pipeline(config)

    if retry:
        pipeline.execute_from_last_failed_step()
    else:
        pipeline.execute()
    if resume:
        pipeline.resume(run_id=run_id)
    else:
        pipeline.execute()
