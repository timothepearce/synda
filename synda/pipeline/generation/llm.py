import asyncio
from typing import List, Optional
from sqlmodel import Session

from synda.model.provider import Provider
from synda.model.run import Run
from synda.model.step import Step
from synda.pipeline.async_executor import AsyncExecutor
from synda.model.node import Node
from synda.utils.llm_provider import LLMProvider
from synda.utils.prompt_builder import PromptBuilder
from synda.progress_manager import ProgressManager


class LLM(AsyncExecutor):
    def __init__(self, session: Session, run: Run, step_model: Step):
        super().__init__(session, run, step_model, save_on_completion=False)
        self.progress = ProgressManager("GENERATION")
        self.provider = Provider.get(self.config.parameters.provider)
        self.model = self.config.parameters.model
        
    async def execute_async(
        self, 
        pending_nodes: List[Node], 
        processed_nodes: List[Node],
        batch_size: Optional[int] = None
    ) -> List[Node]:
        """Execute the LLM generation step asynchronously with optional batching."""
        template = self.config.parameters.template
        occurrences = self.config.parameters.occurrences
        instruction_sets = self.config.parameters.instruction_sets
        
        # Get batch size from parameters or use default
        batch_size = batch_size or getattr(self.config.parameters, "batch_size", 10)
        
        # Build node occurrences
        pending_nodes = self._build_node_occurrences(pending_nodes, occurrences)
        
        # Build prompts
        prompts = PromptBuilder.build(
            self.session, template, pending_nodes, instruction_sets=instruction_sets
        )
        
        result = list(processed_nodes)  # Create a copy to avoid modifying the original
        
        with self.progress.task(
            "Generating...",
            len(pending_nodes) + len(processed_nodes),
            completed=len(processed_nodes),
        ) as advance:
            # Process in batches for better performance
            for i in range(0, len(pending_nodes), batch_size):
                batch_nodes = pending_nodes[i:i+batch_size]
                batch_prompts = prompts[i:i+batch_size]
                
                # Use batch processing if available
                llm_answers = await LLMProvider.batch_call_async(
                    provider=self.provider.name,
                    model=self.model,
                    api_key=self.provider.api_key,
                    prompts=batch_prompts,
                    url=self.provider.api_url,
                    temperature=self.config.parameters.temperature,
                    max_tokens=getattr(self.config.parameters, "max_tokens", 512),
                    batch_size=batch_size
                )
                
                # Create result nodes and save them
                for node, llm_answer in zip(batch_nodes, llm_answers):
                    result_node = Node(parent_node_id=node.id, value=llm_answer)
                    self.step_model.save_during_execution(self.session, node, result_node)
                    result.append(result_node)
                    advance()

        return result
    
    def execute(self, pending_nodes: List[Node], processed_nodes: List[Node]) -> List[Node]:
        """Synchronous wrapper for backward compatibility."""
        batch_size = getattr(self.config.parameters, "batch_size", 10)
        return asyncio.run(self.execute_async(pending_nodes, processed_nodes, batch_size))

    @staticmethod
    def _build_node_occurrences(
        pending_nodes: List[Node], occurrences: int
    ) -> List[Node]:
        """Build multiple occurrences of each node for generation."""
        nodes = []
        for node in pending_nodes:
            nodes.extend([node] * occurrences)
        return nodes
