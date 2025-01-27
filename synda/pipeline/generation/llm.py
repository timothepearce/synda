from litellm import completion
from sqlmodel import Session

from synda.model.provider import Provider
from synda.model.step import Step
from synda.pipeline.executor import Executor
from synda.model.node import Node
from synda.progress_manager import ProgressManager


class LLM(Executor):
    def __init__(self, session: Session, step_model: Step):
        super().__init__(session, step_model)
        self.progress = ProgressManager("GENERATION")
        self.provider = Provider.get(self.config.parameters.provider)

    def execute(self, input_data: list[Node]):
        result = []

        with self.progress.task("Generating...", len(input_data)) as advance:
            for node in input_data:
                prompt = self.config.parameters.template.format(chunk=node.value)
                llm_answer = self._call_llm_provider(prompt)
                result.append(Node(parent_node_id=node.id, value=llm_answer))
                advance()

        return result

    def _call_llm_provider(self, prompt: str) -> str:
        response = completion(
            model=f"{self.provider.name}/{self.config.parameters.model}",
            messages=[{"content": prompt, "role": "user"}],
            api_key=self.provider.api_key,
        )

        return response["choices"][0]["message"]["content"]
