from pathlib import Path
import typer
from typing import Optional

from synda.config import Config
from synda.pipeline import Pipeline
from synda.pipeline.async_pipeline import AsyncPipeline


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
    async_mode: bool = typer.Option(
        False, "--async", "-a", help="Run the pipeline in asynchronous mode"
    ),
    batch_size: Optional[int] = typer.Option(
        None, "--batch-size", "-b", help="Batch size for processing nodes"
    ),
    use_ray: bool = typer.Option(
        False, "--ray", help="Use Ray for distributed processing"
    ),
    use_cache: bool = typer.Option(
        True, "--cache/--no-cache", help="Enable/disable step output caching"
    ),
    pause_after_step: Optional[int] = typer.Option(
        None, "--pause-after", "-p", help="Pause execution after the specified step number"
    ),
):
    """Run a pipeline with provided configuration."""
    
    # Set environment variables for Ray and caching
    import os
    os.environ["SYNDA_ENABLE_RAY"] = str(use_ray).lower()
    os.environ["SYNDA_ENABLE_CACHE"] = str(use_cache).lower()
    
    if async_mode:
        # Use the async pipeline
        if retry:
            AsyncPipeline().retry_sync(batch_size=batch_size)
        elif run_id is not None:
            AsyncPipeline().resume_sync(run_id=run_id, batch_size=batch_size)
        else:
            config = Config.load_config(config_file)
            
            # If pause_after_step is specified, modify the pipeline to include only steps up to that point
            if pause_after_step is not None and pause_after_step > 0:
                if len(config.pipeline) >= pause_after_step:
                    config.pipeline = config.pipeline[:pause_after_step]
                    typer.echo(f"Pipeline will pause after step {pause_after_step}")
                else:
                    typer.echo(f"Warning: pause_after_step ({pause_after_step}) is greater than the number of steps ({len(config.pipeline)})")
            
            pipeline = AsyncPipeline(config)
            pipeline.execute_sync(batch_size=batch_size)
    else:
        # Use the original pipeline
        if retry:
            Pipeline().retry()
        elif run_id is not None:
            Pipeline().resume(run_id=run_id)
        else:
            config = Config.load_config(config_file)
            
            # If pause_after_step is specified, modify the pipeline to include only steps up to that point
            if pause_after_step is not None and pause_after_step > 0:
                if len(config.pipeline) >= pause_after_step:
                    config.pipeline = config.pipeline[:pause_after_step]
                    typer.echo(f"Pipeline will pause after step {pause_after_step}")
                else:
                    typer.echo(f"Warning: pause_after_step ({pause_after_step}) is greater than the number of steps ({len(config.pipeline)})")
            
            pipeline = Pipeline(config)
            pipeline.execute()
