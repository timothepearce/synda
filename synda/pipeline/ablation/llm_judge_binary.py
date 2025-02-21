import json
from typing import Literal

from pydantic import BaseModel
from sqlmodel import Session

from synda.model.provider import Provider
from synda.model.run import Run
from synda.model.step import Step
from synda.pipeline.executor import Executor
from synda.model.node import Node
from synda.progress_manager import ProgressManager
from synda.utils.env import is_debug_enabled
from synda.utils.llm_provider import LLMProvider
from synda.utils.prompt_builder import PromptBuilder


class LLMJudgeCriterionBinaryAnswer(BaseModel):
    # @todo hotfix structured generation with ollama doesn't work as expected
    answer: Literal["YES", "NO", "OUI", "NON"]

    def is_positive_answer(self) -> bool:
        return self.answer == "YES" or self.answer == "OUI"


class LLMJudgeBinary(Executor):
    def __init__(self, session: Session, run: Run, step_model: Step):
        super().__init__(session, run, step_model)
        self.progress = ProgressManager("ABLATION")
        self.provider = Provider.get(self.config.parameters.provider)
        self.model = self.config.parameters.model

    # @todo build criteria prompts in a single call
    def execute(self, input_data: list[Node]):
        criteria = self.config.parameters.criteria
        result = []

        with self.progress.task(
            "  Ablating...", len(input_data) * len(criteria)
        ) as advance_node:
            for node in input_data:
                judge_answers = []
                for criterion in criteria:
                    criterion_prompt = PromptBuilder.build(
                        self.session, criterion, [node]
                    )
                    prompt = self._build_binary_judge_prompt(
                        node.value, criterion_prompt
                    )
                    judge_answer = LLMProvider.call(
                        self.provider.name,
                        self.model,
                        self.provider.api_key,
                        prompt,
                        LLMJudgeCriterionBinaryAnswer,
                        url=self.provider.api_url,
                        temperature=self.config.parameters.temperature,
                        format="json",
                    )
                    try:
                        judge_answer = LLMJudgeCriterionBinaryAnswer(
                            **json.loads(judge_answer)
                        )
                    except Exception as e:
                        print(f"Model response format is malformed: {e}")

                    judge_answers.append(judge_answer)
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

    # @todo move the criterion into step parameters
    @staticmethod
    def _build_binary_judge_prompt(candidate: str, criterion: str) -> str:
        return (
            f"You are an expert judge tasked with evaluating synthetic text data.\n"
            f"You are evaluating synthetic data against a given criterion.\n"
            'You must answer ONLY with {"answer": "YES"} or {"answer": "NO"}.\n'
            'ALWAYS answer in english {"answer": "YES"} or {"answer": "NO"}, never in another language.\n'
            'Output {"answer": "YES"} when the criterion is fulfilled.\n'
            'Output {"answer": "NO"} when the criterion is NOT fulfilled.\n'
            f"------\n"
            f"criterion: Is the candidate written in english?\n"
            f"candidate: Great Britain is a bit pretentious to call itself “Great”.\n"
            '{"answer": "YES"}\n'
            f"------\n"
            f"criterion: Does the text contain more than 10 words?\n"
            f"candidate: The cat sleeps.\n"
            '{"answer": "NO"}\n'
            f"------\n"
            f"criterion: Does the text talks about the sun?\n"
            f"candidate: Synda is a synthetic data library.\n"
            '{"answer": "NO"}\n'
            f"------\n"
            f"criterion: {criterion}\n"
            f"candidate: {candidate}\n"
        )
