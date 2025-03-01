from abc import abstractmethod

from sqlmodel import Session

from synda.model.run import Run
from synda.model.step import Step, StepStatus
from synda.model.node import Node


class Executor:
    def __init__(
        self,
        session: Session,
        run: Run,
        step_model: Step,
        save_on_completion: bool = True,
    ):
        self.session = session
        self.run = run
        self.step_model = step_model
        self.config = step_model.get_step_config()
        self.save_on_completion = save_on_completion

    def execute_and_update_step(
        self,
        pending_nodes: list[Node],
        processed_nodes: list[Node],
        restarted_step: bool = False,
    ) -> list[Node]:
        try:
            self.step_model.set_running(
                self.session, pending_nodes, restarted=restarted_step
            )

            output_nodes = self.execute(pending_nodes, processed_nodes)
            if self.save_on_completion:
                self.step_model.save_at_execution_end(
                    self.session, pending_nodes, output_nodes
                )
            else:
                self.step_model.set_completed(session=self.session)

            filtered_nodes = [node for node in output_nodes if not node.ablated]

            return filtered_nodes
        except Exception as e:
            self.step_model.set_status(self.session, StepStatus.ERRORED)
            raise e

    @abstractmethod
    def execute(self, pending_nodes: list[Node], processed_nodes: list[Node]):
        pass
