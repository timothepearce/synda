from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, model_validator
from sqlmodel import Session

from synda.model.run import Run
from synda.model.step import Step as ModelStep

if TYPE_CHECKING:
    from synda.pipeline.executor import Executor


class Step(BaseModel, ABC):
    type: str
    method: str
    name: str | None = None
    parameters: dict

    @model_validator(mode="after")
    def set_default_name(self) -> Self:
        if self.name is None:
            self.name = f"{self.type}_{self.method}"
        return self

    @abstractmethod
    def get_executor(
        self, session: Session, run: Run, step_model: ModelStep
    ) -> Executor: ...
