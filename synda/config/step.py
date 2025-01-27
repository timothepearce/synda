from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pydantic import BaseModel

from synda.model.step import Step

if TYPE_CHECKING:
    from synda.pipeline.executor import Executor


class Step(BaseModel, ABC):
    type: str
    method: str
    name: str | None = None
    parameters: dict

    @abstractmethod
    def get_executor(self, step_model: Step) -> "Executor":
        pass
