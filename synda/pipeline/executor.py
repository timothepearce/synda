from abc import abstractmethod

from synda.model.step import Step, StepStatus
from synda.pipeline.node import Node


class Executor:
    def __init__(self, step_model: Step):
        self.step_model = step_model
        self.config = step_model.get_step_config()

    def execute_and_update_step(self, input_data: list[Node]) -> list[Node]:
        try:
            self.step_model.update_execution(status=StepStatus.RUNNING, input_data=input_data)
            output_data = self.execute(input_data)
            self.step_model.update_execution(status=StepStatus.COMPLETED, output_data=output_data)

            return output_data
        except Exception as e:
            self.step_model.update_execution(StepStatus.ERRORED)
            raise e

    @abstractmethod
    def execute(self, input_data: list[Node]):
        pass
