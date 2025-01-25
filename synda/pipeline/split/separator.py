from synda.pipeline.executor import Executor
from synda.pipeline.node import Node
from synda.progress_manager import ProgressManager
from synda.model.step import Step


class Separator(Executor):
    def __init__(self, step_model: Step):
        super().__init__(step_model)
        self.progress = ProgressManager("SPLIT")

    def execute(self, input_data: list[Node]):
        result = []
        separator = self.config.parameters.separator

        with self.progress.task("  Separating...", len(input_data)) as advance:
            # @todo implement version without keeping separator value
            for node in input_data:
                text = node.value
                start = 0
                pos = text.find(separator)

                while pos != -1:
                    chunk = text[start:pos + len(separator)]
                    result.append(Node(parent_node_uuid=node.uuid, value=chunk))

                    start = pos + len(separator)
                    pos = text.find(separator, start)

                if start < len(text):
                    result.append(Node(parent_node_uuid=node.uuid, value=text[start:]))

                advance()

        return result
