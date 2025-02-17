from typing import Literal

from pydantic import BaseModel

from synda.config.output.csv import CSVOutputProperties
from synda.config.output.xls import XLSOutputProperties

from synda.pipeline.output.output_saver import OutputSaver


class Output(BaseModel):
    type: Literal["csv", "xls"]
    properties: CSVOutputProperties | XLSOutputProperties

    def get_saver(self) -> OutputSaver:
        if self.type == "csv":
            from synda.pipeline.output.csv_output_saver import CSVOutputSaver

            return CSVOutputSaver(self)

        if self.type == "xls":
            from synda.pipeline.output.xls_output_saver import XLSOutputSaver

            return XLSOutputSaver(self)
