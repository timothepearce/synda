from typing import Literal

from pydantic import BaseModel

from nebula.config.parser import Step


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
            from nebula.pipeline.ablation import LLMJudgeBinary
            return LLMJudgeBinary(self)
