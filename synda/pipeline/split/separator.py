from sqlmodel import Session

from synda.pipeline.executor import Executor
from synda.model.node import Node
from synda.progress_manager import ProgressManager
from synda.model.step import Step


class Separator(Executor):
    def __init__(self, session: Session, step_model: Step):
        super().__init__(session, step_model)
        self.progress = ProgressManager("SPLIT")

    def execute(self, input_data: list[Node]):
        result = []
        separator = self.config.parameters.separator
        keep_separator = self.config.parameters.keep_separator

        with self.progress.task("Separating...", len(input_data)) as advance:
            for node in input_data:
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
