import json
import asyncio
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
    answer: Literal["YES", "NO", "OUI", "NON"]

    def is_positive_answer(self) -> bool:
        return self.answer == "YES" or self.answer == "OUI"


class AsyncLLMJudgeBinary(Executor):
    def __init__(self, session: Session, run: Run, step_model: Step):
        super().__init__(session, run, step_model, save_on_completion=False)
        self.progress = ProgressManager("ABLATION")
        self.provider = Provider.get(self.config.parameters.provider)
        self.model = self.config.parameters.model
        self.batch_size = self.config.parameters.batch_size

    def execute(self, pending_nodes: list[Node], processed_nodes: list[Node]):
        criteria = self.config.parameters.criteria
        result = processed_nodes or []

        if is_debug_enabled():
            print(f"\nTotal nodes to process in async ablation: {len(pending_nodes)}")

        async def judge_node(node):
            judge_answers = []
            for criterion in criteria:
                criterion_prompt = PromptBuilder.build(
                    self.session, criterion, [node]
                )
                prompt = self._build_binary_judge_prompt(
                    node.value, criterion_prompt
                )
                # Appel LLM asynchrone
                loop = asyncio.get_event_loop()
                judge_answer_str = await loop.run_in_executor(
                    None,
                    lambda: LLMProvider.call(
                        self.provider.name,
                        self.model,
                        self.provider.api_key,
                        prompt,
                        LLMJudgeCriterionBinaryAnswer,
                        url=self.provider.api_url,
                        temperature=self.config.parameters.temperature,
                    ),
                )
                try:
                    judge_answer = LLMJudgeCriterionBinaryAnswer(
                        **json.loads(judge_answer_str)
                    )
                except Exception as e:
                    print(f"Model response format is malformed: {e}")
                    judge_answer = LLMJudgeCriterionBinaryAnswer(answer="NO")
                judge_answers.append(judge_answer)
            ablated = not self._check_consensus(judge_answers)
            result_node = Node(
                parent_node_id=node.id, value=node.value, ablated=ablated
            )
            self.step_model.save_during_execution(self.session, node, result_node)
            if is_debug_enabled():
                print(f"\nProcessing node {node.id}:")
                print(f"Answer: {node.value}")
                print(f"Criteria: {str(criteria)}")
                print(f"Consensus: {self.config.parameters.consensus}")
                print(f"Judge answers: {judge_answers}")
                print(f"Ablated: {result_node.is_ablated_text()}\n")
            return result_node

        num_batches = (len(pending_nodes) + self.batch_size - 1) // self.batch_size
        with self.progress.task(
            "  Async Ablating...",
            num_batches,
            completed=0,
        ) as advance_node:
            loop = asyncio.get_event_loop()
            for i in range(0, len(pending_nodes), self.batch_size):
                batch_nodes = pending_nodes[i:i + self.batch_size]
                tasks = [judge_node(node) for node in batch_nodes]
                result_nodes = loop.run_until_complete(asyncio.gather(*tasks))
                result.extend(result_nodes)
                advance_node()  # Avancer d'une unité pour chaque batch traité
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
            f"candidate: Great Britain is a bit pretentious to call itself \"Great\".\n"
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