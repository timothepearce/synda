import json
import asyncio
from typing import Literal, Optional

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
        super().__init__(session, run, step_model, save_on_completion=False)
        self.progress = ProgressManager("ABLATION")
        self.provider = Provider.get(self.config.parameters.provider)
        self.model = self.config.parameters.model
        self.batch = self.config.parameters.batch
        self.batch_size = self.config.parameters.batch_size

    def execute(self, pending_nodes: list[Node], processed_nodes: list[Node]):
        criteria = self.config.parameters.criteria
        result = processed_nodes or []

        if not self.batch or self.batch_size is None:
            result = self._execute_sequential(pending_nodes, processed_nodes, criteria)
        else:
            result = self._execute_batch(pending_nodes, processed_nodes, criteria)
        
        return result

    def _execute_sequential(self, pending_nodes: list[Node], processed_nodes: list[Node], criteria: list[str]) -> list[Node]:
        result = processed_nodes or []
        
        with self.progress.task(
            "  Ablating...",
            (len(pending_nodes) + len(processed_nodes)) * len(criteria),
            completed=len(processed_nodes) * len(criteria),
        ) as advance_node:
            for node in pending_nodes:
                judge_answers = self._evaluate_node_criteria(node, criteria, advance_node)
                result_node = self._create_result_node(node, judge_answers)
                result.append(result_node)
                
                self._log_debug_info(node, criteria, judge_answers, result_node)
                
        return result

    def _execute_batch(self, pending_nodes: list[Node], processed_nodes: list[Node], criteria: list[str]) -> list[Node]:
        result = processed_nodes or []
        num_batches = (len(pending_nodes) + self.batch_size - 1) // self.batch_size
        with self.progress.task(
            "  Ablating...",
            num_batches,
            completed=0,
        ) as advance_node:
            loop = asyncio.get_event_loop()
            for i in range(0, len(pending_nodes), self.batch_size):
                batch_nodes = pending_nodes[i:i + self.batch_size]
                tasks = [self._judge_node_async(node, criteria) for node in batch_nodes]
                result_nodes = loop.run_until_complete(asyncio.gather(*tasks))
                result.extend(result_nodes)
                advance_node()
                
        return result

    def _evaluate_node_criteria(self, node: Node, criteria: list[str], advance_callback=None) -> list[LLMJudgeCriterionBinaryAnswer]:
        judge_answers = []
        for criterion in criteria:
            criterion_prompt = PromptBuilder.build(self.session, criterion, [node])
            prompt = self._build_binary_judge_prompt(node.value, criterion_prompt)
            
            judge_answer = LLMProvider.call(
                self.provider.name,
                self.model,
                self.provider.api_key,
                prompt,
                LLMJudgeCriterionBinaryAnswer,
                url=self.provider.api_url,
                temperature=self.config.parameters.temperature,
            )
            
            judge_answer = self._parse_judge_answer(judge_answer)
            judge_answers.append(judge_answer)
            
            if advance_callback:
                advance_callback()
                
        return judge_answers

    async def _judge_node_async(self, node: Node, criteria: list[str]) -> Node:
        judge_answers = []
        for criterion in criteria:
            criterion_prompt = PromptBuilder.build(self.session, criterion, [node])
            prompt = self._build_binary_judge_prompt(node.value, criterion_prompt)
            
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
            
            judge_answer = self._parse_judge_answer(judge_answer_str)
            judge_answers.append(judge_answer)
            
        result_node = self._create_result_node(node, judge_answers)
        self._log_debug_info(node, criteria, judge_answers, result_node)
        
        return result_node

    def _create_result_node(self, node: Node, judge_answers: list[LLMJudgeCriterionBinaryAnswer]) -> Node:
        ablated = not self._check_consensus(judge_answers)
        result_node = Node(
            parent_node_id=node.id, value=node.value, ablated=ablated
        )
        self.step_model.save_during_execution(self.session, node, result_node)
        return result_node

    def _parse_judge_answer(self, judge_answer_str: str) -> LLMJudgeCriterionBinaryAnswer:
        try:
            return LLMJudgeCriterionBinaryAnswer(**json.loads(judge_answer_str))
        except Exception as e:
            print(f"Model response format is malformed: {e}")
            return LLMJudgeCriterionBinaryAnswer(answer="NO")

    def _log_debug_info(self, node: Node, criteria: list[str], judge_answers: list[LLMJudgeCriterionBinaryAnswer], result_node: Node) -> None:
        if is_debug_enabled():
            print(f"\nProcessing node {node.id}:")
            print(f"Answer: {node.value}")
            print(f"Criteria: {str(criteria)}")
            print(f"Consensus: {self.config.parameters.consensus}")
            print(f"Judge answers: {judge_answers}")
            print(f"Ablated: {result_node.is_ablated_text()}\n")

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
