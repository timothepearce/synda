from nebula.config.parser.split import Split
from nebula.pipeline.executor import Executor
from nebula.pipeline.pipeline_context import PipelineContext


class Chunk(Executor):
    def __init__(self, config: Split):
        super().__init__(config)

    def execute(self, pipeline_context: PipelineContext):
        input_data = pipeline_context.current_data
        chunks: list[str] = []

        size = self.config.parameters.get("size", 500)
        text = input_data

        while text:
            chunks.append(text[:size])
            text = text[size:]

        pipeline_context.add_step_result(
            step_type=self.config.type,
            input_data=input_data,
            output_data=chunks,
            metadata={
                "method": self.config.method,
                "parameters": self.config.parameters
            }
        )

        return pipeline_context
