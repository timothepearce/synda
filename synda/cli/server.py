import typer
from typing import Optional


def server_command(
    host: str = typer.Option(
        "0.0.0.0", "--host", "-h", help="Host to bind the server to"
    ),
    port: int = typer.Option(
        8000, "--port", "-p", help="Port to bind the server to"
    ),
):
    """Start the Synda API server."""
    from synda.api.app import start_api
    
    typer.echo(f"Starting Synda API server on {host}:{port}")
    start_api(host=host, port=port)