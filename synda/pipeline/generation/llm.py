from litellm import completion
from sqlmodel import Session

from synda.model.provider import Provider
from synda.model.run import Run
from synda.model.step import Step
from synda.pipeline.executor import Executor
from synda.model.node import Node
from synda.utils.template_parser import TemplateParser
from synda.progress_manager import ProgressManager


class LLM(Executor):
    def __init__(self, session: Session, run: Run, step_model: Step):
        super().__init__(session, run, step_model)
        self.progress = ProgressManager("GENERATION")
        self.provider = Provider.get(self.config.parameters.provider)

    def execute(self, input_data: list[Node]):
        template = self.config.parameters.template
        prompts = TemplateParser.build_prompts(self.session, template, input_data)
        result = []

        with self.progress.task("Generating...", len(input_data)) as advance:
            for node, prompt in zip(input_data, prompts):
                llm_answer = self._call_llm_provider(prompt)
                result.append(Node(parent_node_id=node.id, value=llm_answer))
                advance()

        return result

    # @todo move to a distinct class
    # @todo use in all steps with a LLM call
    def _call_llm_provider(self, prompt: str) -> str:
        response = completion(
            model=f"{self.provider.name}/{self.config.parameters.model}",
            messages=[{"content": prompt, "role": "user"}],
            api_key=self.provider.api_key,
        )

        return response["choices"][0]["message"]["content"]
