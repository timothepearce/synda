from litellm import completion

from synda.config.generation import Generation
from synda.pipeline.executor import Executor
from synda.pipeline.node import Node
from synda.pipeline.pipeline_context import PipelineContext
from synda.progress_manager import ProgressManager


class LLM(Executor):
    def __init__(self, config: Generation):
        super().__init__(config)
        self.progress = ProgressManager("GENERATION")

    def execute(self, pipeline_context: PipelineContext):
        nodes = pipeline_context.current_data
        result = []

        with self.progress.task("Generating...", len(nodes)) as advance:
            for node in nodes:
                prompt = self.config.parameters.template.format(chunk=node.value)
                llm_answer = self._call_llm_provider(prompt)
                result.append(Node(value=llm_answer, from_node=node))
                advance()

        pipeline_context.add_step_result(
            step_type=self.config.type,
            step_method=self.config.method,
            input_data=nodes,
            output_data=result,
            metadata=self.config.model_dump(),
        )

    def _call_llm_provider(self, prompt: str) -> str:
        response = completion(
            model=f"{self.config.parameters.provider}/{self.config.parameters.model}",
            messages=[{"content": prompt, "role": "user"}]
        )

        return response['choices'][0]['message']['content']
