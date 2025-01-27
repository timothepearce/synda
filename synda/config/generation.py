from typing import Literal

from pydantic import BaseModel
from sqlmodel import Session

from synda.config.step import Step
from synda.model.step import Step as StepModel


class GenerationParameters(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    template: str


class Generation(Step):
    type: str = "generation"
    method: Literal["llm"]
    parameters: GenerationParameters

    def get_executor(self, session: Session, step_model: StepModel):
        if self.method == "llm":
            from synda.pipeline.generation import LLM

            return LLM(session, step_model)
