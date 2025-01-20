import typer
from dotenv import load_dotenv

from synda.database import init_db
from synda.cli.provider import provider_command
from synda.cli.generate import generate_command


app = typer.Typer(
    name="synda",
    help="A synthetic data generator pipeline CLI.",
    add_completion=False,
)

app.command("provider")(provider_command)
app.command("generate")(generate_command)


def main():
    load_dotenv()
    init_db()
    app()
