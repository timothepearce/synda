from litellm import completion

from synda.config.generation import Generation
from synda.pipeline.executor import Executor
from synda.pipeline.pipeline_context import PipelineContext


class LLM(Executor):
    def __init__(self, config: Generation):
        super().__init__(config)

    def execute(self, pipeline_context: PipelineContext):
        documents = pipeline_context.current_data
        documents_llm_generation: list[list[str]] = []

        for document_chunks in documents:
            document_llm_generation = []

            for chunk in document_chunks:
                prompt = self.config.parameters.template.format(chunk=chunk)
                document_llm_generation.append(self._call_llm_provider(prompt))

            documents_llm_generation.append(document_llm_generation)

        pipeline_context.add_step_result(
            step_type=self.config.type,
            input_data=documents,
            output_data=documents_llm_generation,
            metadata={
                "method": self.config.method,
                "parameters": self.config.parameters,
            }
        )

    def _call_llm_provider(self, prompt: str) -> str:
        response = completion(
            model=f"{self.config.parameters.provider}/{self.config.parameters.model}",
            messages=[{"content": prompt, "role": "user"}]
        )

        return response['choices'][0]['message']['content']
