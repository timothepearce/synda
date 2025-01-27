import json
from typing import Literal

from litellm import completion
from pydantic import BaseModel
from sqlmodel import Session

from synda.model.provider import Provider
from synda.model.step import Step
from synda.pipeline.executor import Executor
from synda.model.node import Node
from synda.progress_manager import ProgressManager
from synda.utils import is_debug_enabled


class LLMJudgeCriterionBinaryAnswer(BaseModel):
    answer: Literal["YES", "NO"]

    def is_positive_answer(self) -> bool:
        return self.answer == "YES"


class LLMJudgeBinary(Executor):
    def __init__(self, session: Session, step_model: Step):
        super().__init__(session, step_model)
        self.progress = ProgressManager("ABLATION")
        self.provider = Provider.get(self.config.parameters.provider)

    def execute(self, input_data: list[Node]):
        criteria = self.config.parameters.criteria
        result = []

        with self.progress.task(
            "  Ablating...", len(input_data) * len(criteria)
        ) as advance_node:
            for node in input_data:
                judge_answers = []

                for criterion in criteria:
                    prompt = self._build_binary_judge_prompt(node.value, criterion)
                    response = self._call_llm_provider(prompt)
                    judge_answers.append(response)
                    advance_node()

                ablated = not self._check_consensus(judge_answers)
                result_node = Node(
                    parent_node_id=node.id, value=node.value, ablated=ablated
                )
                result.append(result_node)

                if is_debug_enabled():
                    print(f"Answer: {node.value}")
                    print(f"Criteria: {str(criteria)}")
                    print(f"Consensus: {self.config.parameters.consensus}")
                    print(f"Judge answers: {judge_answers}")
                    print(f"Ablated: {result_node.is_ablated_text()}\n")

        return result

    def _call_llm_provider(self, prompt: str) -> LLMJudgeCriterionBinaryAnswer:
        response = completion(
            model=f"{self.provider.name}/{self.config.parameters.model}",
            messages=[{"content": prompt, "role": "user"}],
            api_key=self.provider.api_key,
            response_format=LLMJudgeCriterionBinaryAnswer,
        )
        answer = json.loads(response["choices"][0]["message"]["content"])
        return LLMJudgeCriterionBinaryAnswer(**answer)

    def _check_consensus(
        self, judge_answers: list[LLMJudgeCriterionBinaryAnswer]
    ) -> bool:
        consensus = self.config.parameters.consensus.lower()
        positive_answers = sum(
            1 for answer in judge_answers if answer.is_positive_answer()
        )
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
