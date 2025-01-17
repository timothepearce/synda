from synda.config.split import Split
from synda.pipeline.executor import Executor
from synda.pipeline.pipeline_context import PipelineContext


class Chunk(Executor):
    def __init__(self, config: Split):
        super().__init__(config)

    def execute(self, pipeline_context: PipelineContext):
        input_data: list[str] = pipeline_context.current_data
        chunks: list[list[str]] = []

        size = self.config.parameters.size

        for text in input_data:
            text_chunks = []
            while text:
                text_chunks.append(text[:size])
                text = text[size:]
            chunks.append(text_chunks)

        pipeline_context.add_step_result(
            step_type=self.config.type,
            input_data=input_data,
            output_data=chunks,
            metadata={
                "method": self.config.method,
                "parameters": self.config.parameters
            }
        )
