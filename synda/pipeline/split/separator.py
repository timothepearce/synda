from sqlmodel import Session

from synda.model.run import Run
from synda.pipeline.executor import Executor
from synda.model.node import Node
from synda.progress_manager import ProgressManager
from synda.model.step import Step


class Separator(Executor):
    def __init__(self, session: Session, run: Run, step_model: Step):
        super().__init__(session, run, step_model)
        self.progress = ProgressManager("SPLIT")

    def execute(self, pending_nodes: list[Node], processed_nodes: list[Node]):
        result = []
        separator = self.config.parameters.separator
        keep_separator = self.config.parameters.keep_separator

        with self.progress.task("Separating...", len(pending_nodes)) as advance:
            for node in pending_nodes:
                text = node.value
                start = 0
                pos = text.find(separator)

                while pos != -1:
                    chunk_end = pos + len(separator) if keep_separator else pos
                    chunk = text[start:chunk_end]

                    if chunk:
                        result.append(Node(parent_node_id=node.id, value=chunk))

                    start = pos + len(separator)
                    pos = text.find(separator, start)

                if start < len(text):
                    result.append(Node(parent_node_id=node.id, value=text[start:]))

                advance()

        return result
