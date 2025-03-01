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

    def execute(self, pending_nodes: list[Node], processed_nodes: list[Node]):
        template = self.config.parameters.template
        occurrences = self.config.parameters.occurrences
        instruction_sets = self.config.parameters.instruction_sets
        pending_nodes = self._build_node_occurrences(pending_nodes, occurrences)
        prompts = PromptBuilder.build(
            self.session, template, pending_nodes, instruction_sets=instruction_sets
        )
        result = processed_nodes
        with self.progress.task(
            "Generating...",
            len(pending_nodes) + len(processed_nodes),
            completed=len(processed_nodes),
        ) as advance:
            for node, prompt in zip(pending_nodes, prompts):
                llm_answer = LLMProvider.call(
                    self.provider.name,
                    self.model,
                    self.provider.api_key,
                    prompt,
                    url=self.provider.api_url,
                    temperature=self.config.parameters.temperature,
                )
                result_node = Node(parent_node_id=node.id, value=llm_answer)
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
