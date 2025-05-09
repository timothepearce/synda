from datasets import load_dataset
from sqlmodel import Session

from synda.pipeline.input import InputLoader
from synda.config.input import Input
from synda.model.node import Node


class HuggingFaceDatasetLoader(InputLoader):
    def __init__(self, input_config: Input):
        self.properties = input_config.properties
        super().__init__()

    def load(self, session: Session) -> list[Node]:
        dataset = load_dataset(
            self.properties.dataset_name,
            split=self.properties.split
        )
        
        target_list = dataset[self.properties.column_name]
        
        if self.properties.limit is not None:
            target_list = target_list[:self.properties.limit]
            
        result = []

        for value in target_list:
            result.append(Node(value=value))

        self.persist_nodes(session, result)

        return result 