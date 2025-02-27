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
        super().__init__(session, run, step_model, save_at_end=False)
        self.progress = ProgressManager("GENERATION")
        self.provider = Provider.get(self.config.parameters.provider)
        self.model = self.config.parameters.model

    def execute(self, input_data: list[Node], n_treated: int = 0):
        template = self.config.parameters.template
        occurrences = self.config.parameters.occurrences
        instruction_sets = self.config.parameters.instruction_sets
        input_data = self._build_node_occurrences(input_data, occurrences)
        prompts = PromptBuilder.build(
            self.session, template, input_data, instruction_sets=instruction_sets
        )
        result = []
        with self.progress.task("Generating...", len(input_data) + n_treated, completed=n_treated) as advance:
            for node, prompt in zip(input_data, prompts):
                llm_answer = LLMProvider.call(
                    self.provider.name,
                    self.model,
                    self.provider.api_key,
                    prompt,
                    url=self.provider.api_url,
                    temperature=self.config.parameters.temperature,
                )
                result_node = Node(parent_node_id=node.id, value=llm_answer)
                self.step_model.save_at_running(self.session, node, result_node)
                result.append(result_node)
                advance()

        return result

    @staticmethod
    def _build_node_occurrences(input_data: list[Node], occurrences: int) -> list[Node]:
        nodes = []

        for node in input_data:
            [nodes.append(node) for _ in range(occurrences)]

        return nodes
