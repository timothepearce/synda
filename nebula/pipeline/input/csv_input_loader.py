import pandas as pd

from nebula.pipeline.input import InputLoader
from nebula.config.input import Input


class CSVInputLoader(InputLoader):
    def __init__(self, input_config: Input):
        self.properties = input_config.properties
        super().__init__()

    def load(self):
        df = pd.read_csv(
            self.properties.path,
            sep=self.properties.separator
        )
        return df[self.properties.target_column]
