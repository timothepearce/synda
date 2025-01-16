import pandas as pd

from nebula.config.output import Output
from nebula.pipeline.output.output_saver import OutputSaver
from nebula.pipeline.pipeline_context import PipelineContext


class CSVOutputSaver(OutputSaver):
    def __init__(self, output_config: Output):
        self.properties = output_config.properties
        super().__init__()

    def save(self, pipeline_context: PipelineContext) -> None:
        synthetic_data = [item for sublist in pipeline_context.current_data for item in sublist]

        df = pd.DataFrame({
            'synthetic data': synthetic_data,
        })

        df.to_csv(
            self.properties.path,
            sep=self.properties.separator,
            index=False
        )
