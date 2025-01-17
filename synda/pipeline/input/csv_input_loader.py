import pandas as pd

from synda.pipeline.input import InputLoader
from synda.config.input import Input
from synda.pipeline.node import Node
from synda.pipeline.pipeline_context import PipelineContext


class CSVInputLoader(InputLoader):
    def __init__(self, input_config: Input):
        self.properties = input_config.properties
        super().__init__()

    def load(self, pipeline_context: PipelineContext) -> list[Node]:
        df = pd.read_csv(
            self.properties.path,
            sep=self.properties.separator
        )
        target_list = df[self.properties.target_column]
        result = []

        for value in target_list.values:
            result.append(Node(value=value, from_node=None))

        pipeline_context.add_step_result(
            step_type="loader",
            step_method="csv",
            input_data=None,
            output_data=result,
            metadata=self.properties.model_dump()
        )
