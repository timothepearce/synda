from pathlib import Path

import typer
from dotenv import load_dotenv

from synda.config import Config
from synda.database import init_db
from synda.pipeline import Pipeline


app = typer.Typer(
    name="synda",
    help="Synthetic data generator pipeline",
    add_completion=False,
)


@app.command("generate")
def generate(
    input_file: Path = typer.Option(
        ...,
        "--input", "-i",
        help="Path to YAML configuration file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
):
    """Generate synthetic data based on a config file"""
    config = Config.load_config(str(input_file))
    pipeline = Pipeline(config)
    pipeline.execute()


def main():
    load_dotenv()
    init_db()
    app()


if __name__ == "__main__":
    main()
