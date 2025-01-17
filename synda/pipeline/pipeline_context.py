import os
from pprint import pprint

from dataclasses import dataclass

from synda.utils import is_debug_enabled


@dataclass
class StepResult:
    step_type: str
    input_data: any
    output_data: any
    metadata: dict[str, any] = None


@dataclass
class PipelineContext:
    current_data: any
    history: list[StepResult]

    def add_step_result(self, step_type: str, input_data: any, output_data: any, metadata: dict[str, any] = None):
        step_result = StepResult(
            step_type=step_type,
            input_data=input_data,
            output_data=output_data,
            metadata=metadata or {}
        )
        self.history.append(step_result)
        self.current_data = output_data

        if is_debug_enabled():
            print(f"{step_type} result:")
            pprint(step_result)
            print("\n")
