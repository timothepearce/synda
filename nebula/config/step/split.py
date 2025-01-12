from nebula.config.step import Step
from nebula.pipeline.pipeline_context import PipelineContext


class Split(Step):
    type: str = "split"
    method: str
    parameters: dict

    def execute(self, pipeline_data: PipelineContext) -> PipelineContext:
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
