from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

if TYPE_CHECKING:
    from synda.pipeline.executor import Executor


class Step(BaseModel, ABC):
    type: str
    method: str
    parameters: Any  # @todo unify with common type

    @abstractmethod
    def get_executor(self) -> "Executor":
        pass
