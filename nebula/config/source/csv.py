import os

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, model_validator


class CSVSourceProperties(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    path: str
    target_column: str
    separator: str = Field(default=";")

    data: pd.DataFrame | None = Field(default=None)

    @model_validator(mode='after')
    def validate_and_load(self) -> 'CSVSourceProperties':
        self._validate_path()
        self.data = self._load_and_validate_csv()
        return self

    def _validate_path(self) -> None:
        if not os.path.isfile(self.path):
            raise ValueError(f"Source file does not exist: {self.path}")

    def _load_and_validate_csv(self) -> pd.DataFrame:
        try:
            df = pd.read_csv(self.path, sep=self.separator)
            if self.target_column not in df.columns:
                raise ValueError(f"Target column '{self.target_column}' not found in CSV file. Available columns: {', '.join(df.columns)}")
            return df

        except pd.errors.EmptyDataError:
            raise ValueError(f"CSV file is empty: {self.path}")

        except pd.errors.ParserError:
            raise ValueError(f"Unable to parse CSV file: {self.path}")
