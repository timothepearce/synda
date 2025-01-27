from abc import abstractmethod

from synda.model.node import Node


class OutputSaver:
    @abstractmethod
    def save(self, input_data: list[Node]):
        pass
