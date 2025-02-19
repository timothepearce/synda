from typing import Any

import pandas as pd

from synda.config.output import Output
from synda.model.node import Node
from synda.pipeline.output.output_saver import OutputSaver


class CSVOutputSaver(OutputSaver):
    def __init__(self, output_config: Output):
        self.properties = output_config.properties
        super().__init__()

    def save(self, input_data: list[Node]) -> None:
        data: dict[str, list] = {}

        for column in self.properties.columns:
            data[column] = [
                self._get_node_attribute(node, column) for node in input_data
            ]

        df = pd.DataFrame(data)

        df.to_csv(self.properties.path, sep=self.properties.separator, index=False)

    @staticmethod
    def _get_node_attribute(node: Node, column: str) -> Any:
        if column == "value":
            return node.value
        elif column == "ablated":
            return node.is_ablated_text()
        elif column == "metadata":
            return node.node_metadata
        else:
            raise ValueError(f"Unknown column: {column}")
