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
    def task(self, description: str, total: int, transient: bool = False):
        with self.progress as progress:
            task_id = progress.add_task(description, total=total, transient=transient)
            yield lambda: progress.advance(task_id)
