from abc import abstractmethod

from sqlmodel import Session

from synda.model.run import Run
from synda.model.step import Step, StepStatus
from synda.model.node import Node


class Executor:
    def __init__(self, session: Session, run: Run, step_model: Step, save_at_end: bool=True):
        self.session = session
        self.run = run
        self.step_model = step_model
        self.config = step_model.get_step_config()
        self.save_at_end = save_at_end

    def execute_and_update_step(
        self, input_nodes: list[Node], restarted: bool = False, n_treated: int = 0
    ) -> list[Node]:
        try:
            self.step_model.set_running(self.session, input_nodes, restarted=restarted)

            output_nodes = self.execute(input_nodes, n_treated)
            if self.save_at_end:
                self.step_model.set_completed_at_the_end(self.session, input_nodes, output_nodes)
            else:
                self.step_model.set_completed(session=self.session)

            filtered_nodes = [node for node in output_nodes if not node.ablated]

            return filtered_nodes
        except Exception as e:
            self.step_model.set_status(self.session, StepStatus.ERRORED)
            raise e

    @abstractmethod
    def execute(self, input_data: list[Node], n_treated: int = 0):
        pass
