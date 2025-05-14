from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum
from pathlib import Path

import pandas as pd
import PyPDF2
from pydantic import BaseModel, Field, FilePath
from sqlmodel import Session

from synda.model.node import Node


class InputFormat(StrEnum):
    CSV = "csv"
    XLS = "xls"
    PDF = "pdf"


class InputConfig(BaseModel):
    format: InputFormat
    path: FilePath
    target_column: str | None = None
    separator: str = ";"
    sheet_name: str = "Sheet1"
    pages: list[str] = Field(default_factory=list)

    def load_csv(self, session: Session) -> list[Node]:
        df = pd.read_csv(self.path, sep=self.separator)
        _check_column(path=self.path, columns=df.columns, target=self.target_column)

        nodes = [Node(value=value) for value in df[self.target_column].values]
        return _persist_nodes(session, nodes)

    def load_xls(self, session: Session) -> list[Node]:
        df = pd.read_excel(self.path, sheet_name=self.sheet_name)
        _check_column(path=self.path, columns=df.columns, target=self.target_column)

        nodes = [Node(value=value) for value in df[self.target_column].values]
        return _persist_nodes(session, nodes)

    def load_pdf(self, session: Session) -> list[Node]:
        with self.path.open("rb") as f:
            reader = PyPDF2.PdfReader(f)
            total_pages = len(reader.pages)
            indices = _get_page_indices(self.pages, total_pages)

            nodes = []
            for idx in indices:
                page = reader.pages[idx]
                text = page.extract_text()

                nodes.append(
                    Node(
                        value=text,
                        node_metadata=[
                            {
                                "source_type": "pdf",
                                "source_path": str(self.path),
                                "page_number": idx + 1,
                                "total_pages": total_pages,
                            }
                        ],
                    )
                )

        return _persist_nodes(session, nodes)

    def load_nodes(self, session: Session) -> list[Node]:
        match self.format:
            case InputFormat.CSV:
                return self.load_csv(session)
            case InputFormat.XLS:
                return self.load_xls(session)
            case InputFormat.PDF:
                return self.load_pdf(session)


def _check_column(path: Path, columns: Iterable[str], target: str | None) -> None:
    if not target or target not in columns:
        raise ValueError(
            f"Column '{target}' not found in {path}. "
            f"Available columns: {', '.join(columns)}"
        )


def _get_page_indices(pages: list[str], total: int) -> list[int]:
    if not pages:
        return list(range(total))

    indices = set()
    for spec in pages:
        if "-" in spec:
            start, end = map(int, spec.split("-"))
            indices.update(range(start - 1, end))
        else:
            indices.add(int(spec) - 1)

    return [i for i in sorted(indices) if 0 <= i < total]


def _persist_nodes(session: Session, nodes: list[Node]) -> list[Node]:
    for node in nodes:
        session.add(node)
    session.flush()

    for node in nodes:
        node.ancestors = {"source": node.id}
        session.add(node)
    session.commit()

    for node in nodes:
        session.refresh(node)

    return nodes
