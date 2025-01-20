from typing import Literal

from pydantic import BaseModel

from synda.config.output.csv import CSVOutputProperties

from synda.pipeline.output.output_saver import OutputSaver


class Output(BaseModel):
    type: Literal["csv"]
    properties: CSVOutputProperties

    def get_saver(self) -> OutputSaver:
        if self.type == "csv":
            from synda.pipeline.output.csv_output_saver import CSVOutputSaver

            return CSVOutputSaver(self)
