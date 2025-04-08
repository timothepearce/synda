import typer
from enum import Enum

from synda.utils.cache import StepCache


class CacheAction(str, Enum):
    CLEAR = "clear"
    INFO = "info"


def cache_command(
    action: CacheAction = typer.Argument(
        ..., help="Action to perform: clear or info"
    ),
    step_id: int = typer.Option(
        None, "--step", "-s", help="Step ID to clear cache for (optional)"
    ),
):
    """Manage the Synda cache."""
    cache = StepCache()
    
    if action == CacheAction.CLEAR:
        if step_id:
            cache.clear_for_step(step_id)
            typer.echo(f"Cache cleared for step {step_id}")
        else:
            cache.clear()
            typer.echo("Cache cleared")
    elif action == CacheAction.INFO:
        # Get cache info
        cache_size = len(cache._cache)
        cache_dir = cache._cache.directory
        
        typer.echo(f"Cache directory: {cache_dir}")
        typer.echo(f"Cache entries: {cache_size}")
        
        # Show cache statistics if available
        if hasattr(cache._cache, "stats"):
            stats = cache._cache.stats()
            typer.echo(f"Cache hits: {stats.get('hits', 0)}")
            typer.echo(f"Cache misses: {stats.get('misses', 0)}")
            typer.echo(f"Cache size: {stats.get('size', 0)} bytes")