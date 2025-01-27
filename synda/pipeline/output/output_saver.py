from abc import abstractmethod

from synda.pipeline.node import Node


class OutputSaver:
    @abstractmethod
    def save(self, input_data: list[Node]):
        pass
