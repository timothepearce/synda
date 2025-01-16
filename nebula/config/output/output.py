from typing import Literal

from pydantic import BaseModel

from nebula.config.output.csv import CSVOutputProperties

from nebula.pipeline.output.output_saver import OutputSaver


class Output(BaseModel):
    type: Literal["csv"]
    properties: CSVOutputProperties

    def get_saver(self) -> OutputSaver:
        if self.type == "csv":
            from nebula.pipeline.output.csv_output_saver import CSVOutputSaver
            return CSVOutputSaver(self)
