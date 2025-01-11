from abc import ABC, abstractmethod

from pydantic import BaseModel


class Step(BaseModel, ABC):
    type: str

    @abstractmethod
    def execute(self) -> None:
        pass

