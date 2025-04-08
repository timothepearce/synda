import typer
from dotenv import load_dotenv

from synda.database import init_db
from synda.cli.provider import provider_command
from synda.cli.generate import generate_command
from synda.cli.server import server_command
from synda.cli.cache import cache_command


app = typer.Typer(
    name="synda",
    help="A synthetic data generator pipeline CLI.",
    add_completion=False,
)

app.command("provider")(provider_command)
app.command("generate")(generate_command)
app.command("server")(server_command)
app.command("cache")(cache_command)


def main():
    load_dotenv()
    init_db()
    app()
