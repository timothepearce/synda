from typing import Literal

from pydantic import BaseModel

from synda.config.input.csv import CSVInputProperties
from synda.config.input.xls import XLSInputProperties
from synda.config.input.pdf import PDFInputProperties
from synda.config.input.database import DatabaseInputProperties
from synda.config.input.huggingface import HuggingFaceInputProperties

from synda.pipeline.input import InputLoader


class Input(BaseModel):
    type: Literal["csv", "xls", "pdf", "huggingface"]
    properties: CSVInputProperties | XLSInputProperties | PDFInputProperties | HuggingFaceInputProperties  # | DatabaseSourceProperties

    def get_loader(self) -> InputLoader:
        if self.type == "csv":
            from synda.pipeline.input.csv_input_loader import CSVInputLoader

            return CSVInputLoader(self)
        elif self.type == "xls":
            from synda.pipeline.input.xls_input_loader import XLSInputLoader

            return XLSInputLoader(self)
        elif self.type == "pdf":
            from synda.pipeline.input.pdf_input_loader import PDFInputLoader
            
            return PDFInputLoader(self)
        elif self.type == "huggingface":
            from synda.pipeline.input.huggingface_input_loader import HuggingFaceDatasetLoader
            
            return HuggingFaceDatasetLoader(self)
