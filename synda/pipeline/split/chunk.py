from sqlmodel import Session

from synda.pipeline.executor import Executor
from synda.model.node import Node
from synda.progress_manager import ProgressManager
from synda.model.step import Step


class Chunk(Executor):
    def __init__(self, session: Session, step_model: Step):
        super().__init__(session, step_model)
        self.progress = ProgressManager("SPLIT")

    def execute(self, input_data: list[Node]):
        result = []
        size = self.config.parameters.size

        with self.progress.task("  Chunking...", len(input_data)) as advance:
            for node in input_data:
                text = node.value

                while text:
                    chunk = text[:size]
                    text = text[size:]
                    result.append(Node(parent_node_id=node.id, value=chunk))

                advance()

        return result
