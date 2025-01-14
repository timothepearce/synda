import os
from typing import TYPE_CHECKING

from nebula.pipeline.pipeline_context import PipelineContext
from nebula.utils import is_debug_enabled

if TYPE_CHECKING:
    from nebula.config import Config


class Pipeline:
    def __init__(self, config: "Config"):
        self.config = config
        self.pipeline = config.pipeline
        self.data: PipelineContext = None

    def execute(self):
        initial_data = self._load_source_data()
        self.data = PipelineContext(
            current_data=initial_data,
            history=[]
        )

        for parser in self.pipeline:
            if is_debug_enabled():
                print(parser)
            executor = parser.get_executor()
            executor.execute(self.data)

    # @todo move into a source class loader
    def _load_source_data(self) -> str:
        input = self.config.input
        if input.type == "csv":
            import pandas as pd
            df = pd.read_csv(
                input.properties.path,
                sep=input.properties.separator
            )
            return df[input.properties.target_column].values[0]

        raise ValueError(f"Source type '{input.type}' not supported")
