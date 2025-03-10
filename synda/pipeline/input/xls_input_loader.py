import pandas as pd

from sqlmodel import Session

from synda.pipeline.input import InputLoader
from synda.config.input import Input
from synda.model.node import Node


class XLSInputLoader(InputLoader):
    def __init__(self, input_config: Input):
        self.properties = input_config.properties
        super().__init__()

    def load(self, session: Session) -> list[Node]:
        df = pd.read_excel(self.properties.path, sheet_name=self.properties.sheet_name)
        target_list = df[self.properties.target_column]
        result = []

        for value in target_list.values:
            result.append(Node(value=value))

        self.persist_nodes(session, result)

        return result
