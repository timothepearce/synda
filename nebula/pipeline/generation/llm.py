import os

# from litellm import completion

from nebula.config.parser.generation import Generation
from nebula.pipeline.executor import Executor
from nebula.pipeline.pipeline_context import PipelineContext


class LLM(Executor):
    def __init__(self, config: Generation):
        super().__init__(config)

    def execute(self, pipeline_context: PipelineContext):
        input_data = pipeline_context.current_data
        llm_generation: list[str] = []

        # @todo build prompt
        # @todo implement call with litellm
        # @todo downgrade litellm to avoid warning from pydantic v1

        for text in input_data:
            llm_generation.append("mocked llm answer")

        pipeline_context.add_step_result(
            step_type=self.config.type,
            input_data=input_data,
            output_data=llm_generation,
            metadata={
                "method": self.config.method,
                "parameters": self.config.parameters
            }
        )