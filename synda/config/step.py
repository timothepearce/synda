from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pydantic import BaseModel, model_validator
from sqlmodel import Session

from synda.model.run import Run
from synda.model.step import Step

if TYPE_CHECKING:
    from synda.pipeline.executor import Executor


class Step(BaseModel, ABC):
    type: str
    method: str
    name: str | None = None
    parameters: dict

    @model_validator(mode="after")
    def set_default_name(self) -> str:
        if self.name is None:
            self.name = f"{self.type}_{self.method}"
        return self

    @abstractmethod
    def get_executor(self, session: Session, run: Run, step_model: Step) -> "Executor":
        pass
