import json
from typing import Literal

from litellm import completion
from pydantic import BaseModel

from synda.config.generation import Generation
from synda.pipeline.executor import Executor
from synda.pipeline.node import Node
from synda.pipeline.pipeline_context import PipelineContext
from synda.progress_manager import ProgressManager
from synda.utils import is_debug_enabled


class LLMJudgeCriterionBinaryAnswer(BaseModel):
    answer: Literal["YES", "NO"]

    def is_positive_answer(self) -> bool:
        return self.answer == "YES"


class LLMJudgeBinary(Executor):
    def __init__(self, config: Generation):
        super().__init__(config)
        self.progress = ProgressManager("ABLATION")

    def execute(self, pipeline_context: PipelineContext):
        nodes = pipeline_context.current_data
        criteria = self.config.parameters.criteria
        result = []

        with self.progress.task("  Ablating...", len(nodes) * len(criteria)) as advance_node:
            for node in nodes:
                judge_answers = []

                for criterion in criteria:
                    prompt = self._build_binary_judge_prompt(node.value, criterion)
                    response = self._call_llm_provider(prompt)
                    judge_answers.append(response)
                    advance_node()

                ablated = not self._check_consensus(judge_answers)
                result_node = Node(value=node.value, ablated=ablated, from_node=node)
                result.append(result_node)

                if is_debug_enabled():
                    print(f"Answer: {node.value}")
                    print(f"Criteria: {str(criteria)}")
                    print(f"Consensus: {self.config.parameters.consensus}")
                    print(f"Judge answers: {judge_answers}")
                    print(f"Ablated: {result_node.is_ablated_text()}\n")

        pipeline_context.add_step_result(
            step_type=self.config.type,
            step_method=self.config.method,
            input_data=nodes,
            output_data=result,
            metadata=self.config.model_dump(),
        )

    def _call_llm_provider(self, prompt: str) -> LLMJudgeCriterionBinaryAnswer:
        response = completion(
            model=f"{self.config.parameters.provider}/{self.config.parameters.model}",
            messages=[{"content": prompt, "role": "user"}],
            response_format=LLMJudgeCriterionBinaryAnswer
        )
        answer = json.loads(response['choices'][0]['message']['content'])
        return LLMJudgeCriterionBinaryAnswer(**answer)

    def _check_consensus(self, judge_answers: list[LLMJudgeCriterionBinaryAnswer]) -> bool:
        consensus = self.config.parameters.consensus.lower()
        positive_answers = sum(1 for answer in judge_answers if answer.is_positive_answer())
        total_answers = len(judge_answers)

        if total_answers == 0:
            return False

        match consensus:
            case "all":
                return positive_answers == total_answers
            case "any":
                return positive_answers > 0
            case "majority":
                return positive_answers > total_answers / 2
            case _:
                raise ValueError(f"Unknown consensus: {consensus}")

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
