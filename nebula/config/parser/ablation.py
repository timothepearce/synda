from typing import Literal

from nebula.config.parser import Step


class Ablation(Step):
    type: str = "ablation"
    method: Literal["llm-judge-binary"]

    def get_executor(self):
        if self.method == "llm-judge-binary":
            from nebula.pipeline.ablation import LLMJudgeBinary
            return LLMJudgeBinary(self)
