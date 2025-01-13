from typing import TYPE_CHECKING

from nebula.pipeline.pipeline_context import PipelineContext

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
            executor = parser.get_executor()
            self.data = executor(self.data)

    def _load_source_data(self) -> str:
        source = self.config.source
        if source.type == "csv":
            import pandas as pd
            df = pd.read_csv(
                source.properties.path,
                sep=source.properties.separator
            )
            return df[source.properties.target_column].values[0]

        raise ValueError(f"Source type '{source.type}' not supported")
