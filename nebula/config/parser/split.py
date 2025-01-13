from nebula.config.parser import Step
from nebula.pipeline.pipeline_context import PipelineContext
from nebula.pipeline.split import Chunk


class Split(Step):
    type: str = "split"
    method: str
    parameters: dict

    def validate_config(self) -> bool:
        return True

    def get_executor(self):
        if self.method == "chunk":
            return Chunk()

    def _move_to_executor(self, pipeline_data: PipelineContext):
        input_data = pipeline_data.current_data
        chunks: list[str] = []

        if self.method == "chunk":
            size = self.parameters.get("size", 500)
            text = input_data

            while text:
                chunks.append(text[:size])
                text = text[size:]

        pipeline_data.add_step_result(
            step_type=self.type,
            input_data=input_data,
            output_data=chunks,
            metadata={
                "method": self.method,
                "parameters": self.parameters
            }
        )

        return pipeline_data
