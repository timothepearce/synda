from typing import Literal

from pydantic import BaseModel
from sqlmodel import Session

from synda.config.step import Step
from synda.model.run import Run
from synda.model.step import Step as StepModel


class AblationParameters(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    temperature: float | None = 1.0
    consensus: Literal["all", "any", "majority"]
    criteria: list[str]


class Ablation(Step):
    type: str = "ablation"
    method: Literal["llm-judge-binary"]
    parameters: AblationParameters

    def get_executor(self, session: Session, run: Run, step_model: StepModel):
        if self.method == "llm-judge-binary":
            from synda.pipeline.ablation import LLMJudgeBinary

            return LLMJudgeBinary(session, run, step_model)
