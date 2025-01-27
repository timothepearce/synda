from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlmodel import Session

from synda.model.step import Step

if TYPE_CHECKING:
    from synda.pipeline.executor import Executor


class Step(BaseModel, ABC):
    type: str
    method: str
    name: str | None = None
    parameters: dict

    @abstractmethod
    def get_executor(self, session: Session, step_model: Step) -> "Executor":
        pass
