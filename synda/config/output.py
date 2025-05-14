from __future__ import annotations

from enum import StrEnum, auto
from pathlib import Path

import pandas as pd
from pydantic import BaseModel, Field, model_validator

from synda.model.node import Node


class OutputFormat(StrEnum):
    CSV = auto()
    XLS = auto()


class OutputConfig(BaseModel):
    format: OutputFormat = OutputFormat.CSV
    path: Path
    overwrite: bool = False

    # csv-only
    separator: str = ";"
    columns: list[str] = Field(default_factory=lambda: ["value"])

    # xls-only
    sheet_name: str = "Sheet1"

    @model_validator(mode="after")
    def validate_path(self) -> OutputConfig:
        resolved_path = self.path.resolve()

        if not self.overwrite and resolved_path.is_file():
            raise ValueError(
                f"Output file '{resolved_path}' already exists. "
                "Set 'overwrite: true' to allow overwriting, or provide a different path."
            )

        self.path = resolved_path
        return self

    def save_output(self, nodes: list[Node]) -> None:
        values = [node.value for node in nodes]
        ablated = [node.is_ablated_text() for node in nodes]
        metadata = [node.node_metadata for node in nodes]

        available_columns = {
            "value": values,
            "ablated": ablated,
            "metadata": metadata,
        }

        selected = {
            col: available_columns[col]
            for col in self.columns
            if col in available_columns
        }

        df = pd.DataFrame(selected)

        match self.format:
            case OutputFormat.CSV:
                df.to_csv(self.path, sep=self.separator, index=False)
            case OutputFormat.XLS:
                df.to_excel(self.path, sheet_name=self.sheet_name, index=False)
