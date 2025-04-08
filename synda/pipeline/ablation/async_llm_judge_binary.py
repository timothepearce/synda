import json
import asyncio
from typing import Literal, Optional, List, Dict, Any

from pydantic import BaseModel
from sqlmodel import Session

from synda.model.provider import Provider
from synda.model.run import Run
from synda.model.step import Step
from synda.pipeline.async_executor import AsyncExecutor
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


class AsyncLLMJudgeBinary(AsyncExecutor):
    def __init__(self, session: Session, run: Run, step_model: Step):
        super().__init__(session, run, step_model, save_on_completion=False)
        self.progress = ProgressManager("ABLATION")
        self.provider = Provider.get(self.config.parameters.provider)
        self.model = self.config.parameters.model

    async def execute_async(
        self, 
        pending_nodes: List[Node], 
        processed_nodes: List[Node],
        batch_size: Optional[int] = None
    ) -> List[Node]:
        """Execute the ablation step asynchronously with optional batching."""
        criteria = self.config.parameters.criteria
        result = processed_nodes or []
        
        # Get batch size from parameters or use default
        batch_size = batch_size or getattr(self.config.parameters, "batch_size", 10)

        with self.progress.task(
            "  Ablating...",
            (len(pending_nodes) + len(processed_nodes)) * len(criteria),
            completed=len(processed_nodes) * len(criteria),
        ) as advance_node:
            # Process nodes in batches for better performance
            for i in range(0, len(pending_nodes), batch_size):
                batch_nodes = pending_nodes[i:i+batch_size]
                
                # Process each criterion for all nodes in the batch
                for criterion in criteria:
                    # Build prompts for all nodes in the batch
                    criterion_prompts = []
                    for node in batch_nodes:
                        criterion_prompt = PromptBuilder.build(
                            self.session, criterion, [node]
                        )
                        prompt = self._build_binary_judge_prompt(
                            node.value, criterion_prompt
                        )
                        criterion_prompts.append(prompt)
                    
                    # Call LLM in batch for this criterion
                    judge_answers_batch = await LLMProvider.batch_call_async(
                        provider=self.provider.name,
                        model=self.model,
                        api_key=self.provider.api_key,
                        prompts=criterion_prompts,
                        response_format=LLMJudgeCriterionBinaryAnswer,
                        url=self.provider.api_url,
                        temperature=self.config.parameters.temperature,
                        format="json",
                        batch_size=batch_size
                    )
                    
                    # Process the answers for each node
                    for node_idx, node in enumerate(batch_nodes):
                        # Initialize judge_answers list if this is the first criterion
                        if not hasattr(node, '_judge_answers'):
                            node._judge_answers = []
                        
                        # Parse the answer
                        try:
                            judge_answer = LLMJudgeCriterionBinaryAnswer(
                                **json.loads(judge_answers_batch[node_idx])
                            )
                            node._judge_answers.append(judge_answer)
                        except Exception as e:
                            print(f"Model response format is malformed: {e}")
                            # Add a default "NO" answer in case of parsing error
                            node._judge_answers.append(LLMJudgeCriterionBinaryAnswer(answer="NO"))
                        
                        advance_node()
                
                # Create result nodes for all nodes in the batch
                for node in batch_nodes:
                    ablated = not self._check_consensus(node._judge_answers)
                    result_node = Node(
                        parent_node_id=node.id, value=node.value, ablated=ablated
                    )
                    self.step_model.save_during_execution(self.session, node, result_node)
                    result.append(result_node)
                    
                    if is_debug_enabled():
                        print(f"Answer: {node.value}")
                        print(f"Criteria: {str(criteria)}")
                        print(f"Consensus: {self.config.parameters.consensus}")
                        print(f"Judge answers: {node._judge_answers}")
                        print(f"Ablated: {result_node.is_ablated_text()}\n")
                    
                    # Clean up temporary attribute
                    delattr(node, '_judge_answers')

        return result
    
    def execute(self, pending_nodes: List[Node], processed_nodes: List[Node]) -> List[Node]:
        """Synchronous wrapper for backward compatibility."""
        batch_size = getattr(self.config.parameters, "batch_size", 10)
        return asyncio.run(self.execute_async(pending_nodes, processed_nodes, batch_size))

    def _check_consensus(
        self, judge_answers: List[LLMJudgeCriterionBinaryAnswer]
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
            f"candidate: Great Britain is a bit pretentious to call itself "Great".\n"
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