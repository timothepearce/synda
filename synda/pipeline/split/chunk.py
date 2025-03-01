from sqlmodel import Session

from synda.model.run import Run
from synda.pipeline.executor import Executor
from synda.model.node import Node
from synda.progress_manager import ProgressManager
from synda.model.step import Step


class Chunk(Executor):
    def __init__(self, session: Session, run: Run, step_model: Step):
        super().__init__(session, run, step_model)
        self.progress = ProgressManager("SPLIT")

    def execute(self, pending_nodes: list[Node], processed_nodes: list[Node]):
        result = []
        size = self.config.parameters.size

        with self.progress.task("  Chunking...", len(pending_nodes)) as advance:
            for node in pending_nodes:
                text = node.value

                while text:
                    chunk = text[:size]
                    text = text[size:]
                    result.append(Node(parent_node_id=node.id, value=chunk))

                advance()

        return result
