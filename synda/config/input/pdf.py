import os
from typing import List

import PyPDF2
from pydantic import model_validator, Field

from synda.config.input.input_properties import InputProperties


class PDFInputProperties(InputProperties):
    path: str
    pages: List[str] = Field(default_factory=list)  # Ex: ["1-10", "14-16", "19"]

    @model_validator(mode="after")
    def validate_properties(self) -> "PDFInputProperties":
        self._validate_path()
        self._validate_file()
        return self

    def _validate_path(self) -> None:
        if not os.path.isfile(self.path):
            raise ValueError(f"Source file does not exist: {self.path}")

    def _validate_file(self) -> None:
        try:
            with open(self.path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                if len(reader.pages) == 0:
                    raise ValueError(f"PDF file is empty: {self.path}")
        except Exception as e:
            raise ValueError(f"Unable to parse PDF file: {self.path}. Error: {str(e)}")

    def get_page_indices(self, total_pages: int) -> list[int]:
        """
        Convertit la liste de plages de pages en liste d'index (1-based).
        Si pages est vide, retourne toutes les pages.
        """
        if not self.pages:
            return list(range(total_pages))
        indices = set()
        for entry in self.pages:
            if '-' in entry:
                start, end = entry.split('-')
                indices.update(range(int(start)-1, int(end)))
            else:
                indices.add(int(entry)-1)
        # On filtre les index hors bornes
        return [i for i in sorted(indices) if 0 <= i < total_pages]