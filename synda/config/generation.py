from typing import Literal

from pydantic import BaseModel

from synda.config.step import Step


class GenerationParameters(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    template: str


class Generation(Step):
    type: str = "generation"
    method: Literal["llm"]
    parameters: GenerationParameters

    def get_executor(self):
        if self.method == "llm":
            from synda.pipeline.generation import LLM
            return LLM(self)
