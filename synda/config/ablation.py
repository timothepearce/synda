from typing import Literal

from pydantic import BaseModel
from sqlmodel import Session

from synda.config.step import Step
from synda.model.step import Step as StepModel


class AblationParameters(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    consensus: Literal["all", "any", "majority"]
    criteria: list[str]


class Ablation(Step):
    type: str = "ablation"
    method: Literal["llm-judge-binary"]
    parameters: AblationParameters

    def get_executor(self, session: Session, step_model: StepModel):
        if self.method == "llm-judge-binary":
            from synda.pipeline.ablation import LLMJudgeBinary

            return LLMJudgeBinary(session, step_model)
