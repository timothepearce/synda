from pprint import pprint

from pydantic import BaseModel, Field

from synda.pipeline.node import Node
from synda.utils import is_debug_enabled


class StepResult(BaseModel):
    step_type: str
    step_method: str
    metadata: dict
    input_data: list[Node] | None = None
    output_data: list[Node]


class PipelineContext(BaseModel):
    current_data: list[Node] | None = None
    history: list[StepResult] = Field(default_factory=list)

    def add_step_result(self, step_type: str, step_method: str, input_data: any, output_data: any, metadata: dict):
        step_result = StepResult(
            step_type=step_type,
            step_method=step_method,
            metadata=metadata,
            input_data=input_data,
            output_data=output_data,
        )
        self.history.append(step_result)
        self.current_data = output_data

        if is_debug_enabled():
            print(f"{step_type} result:")
            pprint(step_result)
            print("\n")
