from litellm import completion

from nebula.config.generation import Generation
from nebula.pipeline.executor import Executor
from nebula.pipeline.pipeline_context import PipelineContext


class LLM(Executor):
    def __init__(self, config: Generation):
        super().__init__(config)

    def execute(self, pipeline_context: PipelineContext):
        chunks = pipeline_context.current_data
        prompts: list[str] = []
        llm_generation: list[str] = []

        for chunk in chunks:
            prompt = self.config.parameters.template.format(chunk=chunk)
            prompts.append(prompt)
            llm_generation.append(self._call_llm_provider(prompt))

        pipeline_context.add_step_result(
            step_type=self.config.type,
            input_data=chunks,
            output_data=llm_generation,
            metadata={
                "method": self.config.method,
                "parameters": self.config.parameters,
                "prompts": prompts,
            }
        )

    def _call_llm_provider(self, prompt: str) -> str:
        response = completion(
            model=f"{self.config.parameters.provider}/{self.config.parameters.model}",
            messages=[{"content": prompt, "role": "user"}]
        )

        return response['choices'][0]['message']['content']
