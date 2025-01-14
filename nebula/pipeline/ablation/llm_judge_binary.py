from typing import Literal

from litellm import completion
from pydantic import BaseModel

from nebula.config.parser.generation import Generation
from nebula.pipeline.executor import Executor
from nebula.pipeline.pipeline_context import PipelineContext


class LLMJudgeBinaryAnswer(BaseModel):
    answer: Literal["YES", "NO"]


class LLMJudgeBinary(Executor):
    def __init__(self, config: Generation):
        super().__init__(config)

    def execute(self, pipeline_context: PipelineContext):
        llm_answers = pipeline_context.current_data
        criteria = self.config.parameters.criteria
        prompts: list[list[str]] = []
        judge_answers: list[list[bool]] = []

        for answer in llm_answers:
            for criterion in criteria:
                prompt = self._build_binary_judge_prompt(answer, criterion)
                print(prompt)
                prompts.append(prompt)
                judge_answers.append(self._call_llm_provider(prompt))

        # @todo add filtering

        pipeline_context.add_step_result(
            step_type=self.config.type,
            input_data=llm_answers,
            output_data=judge_answers,
            metadata={
                "method": self.config.method,
                "parameters": self.config.parameters,
                "prompts": prompts,
            }
        )

    @staticmethod
    def _build_binary_judge_prompt(candidate: str, criterion: str) -> str:
        return (
            f"You are an expert judge tasked with evaluating synthetic text data.\n"
            f"You are evaluating synthetic data against a given criterion.\n"
            f"You must answer by YES or NO.\n"
            f"Output YES when the criterion is fulfilled.\n"
            f"Output NO when the criterion is NOT fulfilled.\n"
            f"------\n"
            f"criterion: Is the candidate written in english?\n"
            f"candidate: Great Britain is a bit pretentious to call itself “Great”.\n"
            "{answer: YES}\n"
            f"------\n"
            f"criterion: Does the text contain more than 10 words?\n"
            f"candidate: The cat sleeps.\n"
            "{answer: NO}\n"
            f"------\n"
            f"criterion: {criterion}\n"
            f"candidate: {candidate}\n"
        )

    def _call_llm_provider(self, prompt: str) -> str:
        response = completion(
            model=f"{self.config.parameters.provider}/{self.config.parameters.model}",
            messages=[{"content": prompt, "role": "user"}],
            response_format=LLMJudgeBinaryAnswer
        )
        print(response)

        return response['choices'][0]['message']['content']

