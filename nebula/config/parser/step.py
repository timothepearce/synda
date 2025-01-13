from abc import ABC, abstractmethod

from pydantic import BaseModel


class Step(BaseModel, ABC):
    type: str

    @abstractmethod
    def get_executor(self):
        pass
