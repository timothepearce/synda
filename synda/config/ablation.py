from typing import Literal

from pydantic import BaseModel

from synda.config.step import Step


class AblationParameters(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    consensus: Literal["all", "any", "majority"]
    criteria: list[str]


class Ablation(Step):
    type: str = "ablation"
    method: Literal["llm-judge-binary"]
    parameters: AblationParameters

    def get_executor(self):
        if self.method == "llm-judge-binary":
            from synda.pipeline.ablation import LLMJudgeBinary
            return LLMJudgeBinary(self)
