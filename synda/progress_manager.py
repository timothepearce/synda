from enum import Enum
from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    SpinnerColumn,
    MofNCompleteColumn,
    TimeElapsedColumn,
)
from rich.console import Console
from contextlib import contextmanager


class ExecutorColor(Enum):
    SPLIT = "red"
    GENERATION = "green"
    ABLATION = "cyan"
    CLEAN = "blue"
    METADATA = "yellow"


class ProgressManager:
    def __init__(self, executor_type: str):
        self.console = Console()
        self.color = ExecutorColor[executor_type.upper()].value
        self.progress = Progress(
            SpinnerColumn(speed=2),
            TextColumn(f"[{self.color}]" + "{task.description}", justify="right"),
            BarColumn(),
            MofNCompleteColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
        )

    @contextmanager
    def task(
        self, description: str, total: int, completed: int = 0, batch_size: int = 1, transient: bool = False
    ):
        with self.progress as progress:
            task_id = progress.add_task(
                description, total=total, transient=transient, completed=completed
            )
            def safe_advance():
                remaining = total - progress.tasks[task_id].completed
                progress.advance(task_id, min(batch_size, int(remaining)))

            yield safe_advance
            # yield lambda: progress.advance(task_id, batch_size)
