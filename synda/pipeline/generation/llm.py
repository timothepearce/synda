import asyncio
from sqlmodel import Session

from synda.model.provider import Provider
from synda.model.run import Run
from synda.model.step import Step
from synda.pipeline.executor import Executor
from synda.model.node import Node
from synda.utils.llm_provider import LLMProvider
from synda.utils.prompt_builder import PromptBuilder
from synda.progress_manager import ProgressManager


class LLM(Executor):
    def __init__(self, session: Session, run: Run, step_model: Step):
        super().__init__(session, run, step_model, save_on_completion=False)
        self.progress = ProgressManager("GENERATION")
        self.provider = Provider.get(self.config.parameters.provider)
        self.model = self.config.parameters.model
        self.batch = self.config.parameters.batch
        self.batch_size = self.config.parameters.batch_size

    def execute(self, pending_nodes: list[Node], processed_nodes: list[Node]):
        template = self.config.parameters.template
        occurrences = self.config.parameters.occurrences
        instruction_sets = self.config.parameters.instruction_sets
        instruction_mode = self.config.parameters.instruction_mode
        pending_nodes = self._build_node_occurrences(pending_nodes, occurrences)

        result = processed_nodes
        if not self.batch or self.batch_size is None:
            with self.progress.task(
                "Generating...",
                len(pending_nodes) + len(processed_nodes),
                completed=len(processed_nodes),
            ) as advance:
                for node in pending_nodes:
                    prompts = PromptBuilder.build(
                        self.session,
                        template,
                        [node],
                        instruction_sets=instruction_sets,
                        instruction_mode=instruction_mode
                    )
                    for prompt in prompts:
                        llm_answer = LLMProvider.call(
                            self.provider.name,
                            self.model,
                            self.provider.api_key,
                            prompt,
                            url=self.provider.api_url,
                            temperature=self.config.parameters.temperature,
                        )
                        metadata = prompt
                        result_node = Node(
                            parent_node_id=node.id,
                            value=llm_answer,
                            node_metadata=metadata,
                            ancestors={'source': node.id}
                        )
                        self.step_model.save_during_execution(self.session, node, result_node)
                        result.append(result_node)
                    advance()
        else:
            all_prompts = []
            node_map = {}
            for node in pending_nodes:
                prompts = PromptBuilder.build(
                    self.session,
                    template,
                    [node],
                    instruction_sets=instruction_sets,
                    instruction_mode=instruction_mode
                )
                for prompt in prompts:
                    all_prompts.append(prompt)
                    node_map[prompt] = node
            num_batches = (len(all_prompts) + self.batch_size - 1) // self.batch_size
            with self.progress.task(
                "Generating...",
                num_batches,
                completed=0,
            ) as advance:
                for i in range(0, len(all_prompts), self.batch_size):
                    batch_prompts = all_prompts[i:i + self.batch_size]
                    loop = asyncio.get_event_loop()
                    tasks = [
                        loop.run_in_executor(
                            None,
                            lambda p: LLMProvider.call(
                                self.provider.name,
                                self.model,
                                self.provider.api_key,
                                p,
                                url=self.provider.api_url,
                                temperature=self.config.parameters.temperature
                            ),
                            prompt
                        )
                        for prompt in batch_prompts
                    ]
                    responses = loop.run_until_complete(asyncio.gather(*tasks))
                    for prompt, response in zip(batch_prompts, responses):
                        node = node_map[prompt]
                        result_node = Node(
                            parent_node_id=node.id,
                            value=response,
                            node_metadata=prompt,
                            ancestors={'source': node.id}
                        )
                        self.step_model.save_during_execution(self.session, node, result_node)
                        result.append(result_node)
                    advance()
        return result
    

    @staticmethod
    def _build_node_occurrences(
        pending_nodes: list[Node], occurrences: int
    ) -> list[Node]:
        nodes = []
        for node in pending_nodes:
            [nodes.append(node) for _ in range(occurrences)]
        return nodes
