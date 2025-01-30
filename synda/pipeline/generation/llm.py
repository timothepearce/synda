from litellm import completion
from sqlmodel import Session

from synda.model.provider import Provider
from synda.model.run import Run
from synda.model.step import Step
from synda.pipeline.executor import Executor
from synda.model.node import Node
from synda.pipeline.template.template_parser import TemplateParser
from synda.progress_manager import ProgressManager


class LLM(Executor):
    def __init__(self, session: Session, run: Run, step_model: Step):
        super().__init__(session, run, step_model)
        self.progress = ProgressManager("GENERATION")
        self.provider = Provider.get(self.config.parameters.provider)

    def execute(self, input_data: list[Node]):
        result = []

        prompts = self._build_prompts(input_data)

        with self.progress.task("Generating...", len(input_data)) as advance:
            for node, prompt in zip(input_data, prompts):
                llm_answer = self._call_llm_provider(prompt)
                result.append(Node(parent_node_id=node.id, value=llm_answer))
                advance()

        return result

    def _build_prompts(self, input_data: list[Node]) -> list[str]:
        template = self.config.parameters.template
        variables = TemplateParser.extract_variables(template)
        prompts = []

        parent_node_ids = set()
        for node in input_data:
            for variable_name in variables:
                parent_node_ids.add(node.ancestors[variable_name])

        parent_nodes = Node.get(self.session, list(parent_node_ids))

        for node in input_data:
            variable_value = {}
            for variable_name in variables:
                parent_node_id = node.ancestors[variable_name]
                parent_node = next(node for node in parent_nodes if node.id == parent_node_id)
                variable_value[variable_name] = parent_node.value

            prompts.append(template.format(**variable_value))
            print("VARIABLES: ", variable_value)
            print("\n\n\n")

        return prompts

    def _call_llm_provider(self, prompt: str) -> str:
        response = completion(
            model=f"{self.provider.name}/{self.config.parameters.model}",
            messages=[{"content": prompt, "role": "user"}],
            api_key=self.provider.api_key,
        )

        return response["choices"][0]["message"]["content"]
