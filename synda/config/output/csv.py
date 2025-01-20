import os

from pydantic import Field, model_validator

from synda.config.output.output_properties import OutputProperties


class CSVOutputProperties(OutputProperties):
    path: str
    separator: str = Field(default=";")

    @model_validator(mode="after")
    def validate_properties(self) -> "CSVOutputProperties":
        self._validate_path()
        return self

    def _validate_path(self) -> None:
        if os.path.isfile(self.path):
            raise ValueError(f"Output file already exist: {self.path}")
