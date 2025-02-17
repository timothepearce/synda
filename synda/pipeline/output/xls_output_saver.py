import pandas as pd

from synda.config.output import Output
from synda.model.node import Node
from synda.pipeline.output.output_saver import OutputSaver


class XLSOutputSaver(OutputSaver):
    def __init__(self, output_config: Output):
        self.properties = output_config.properties
        super().__init__()

    def save(self, input_data: list[Node]) -> None:
        synthetic_data = [node.value for node in input_data]
        ablated_data = [node.is_ablated_text() for node in input_data]

        df = pd.DataFrame(
            {
                "synthetic data": synthetic_data,
                "ablated": ablated_data,
            }
        )

        df.to_excel(
            self.properties.path, sheet_name=self.properties.sheet_name, index=False
        )
