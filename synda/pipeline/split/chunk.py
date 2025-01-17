from synda.config.split import Split
from synda.pipeline.executor import Executor
from synda.pipeline.node import Node
from synda.pipeline.pipeline_context import PipelineContext
from synda.progress_manager import ProgressManager


class Chunk(Executor):
    def __init__(self, config: Split):
        super().__init__(config)
        self.progress = ProgressManager("SPLIT")

    def execute(self, pipeline_context: PipelineContext):
        input_nodes = pipeline_context.current_data
        result = []
        size = self.config.parameters.size

        with self.progress.task("  Chunking...", len(input_nodes)) as advance:
            for node in input_nodes:
                text = node.value

                while text:
                    chunk = text[:size]
                    text = text[size:]
                    result.append(Node(value=chunk, from_node=node))

                advance()

        pipeline_context.add_step_result(
            step_type=self.config.type,
            step_method=self.config.method,
            input_data=input_nodes,
            output_data=result,
            metadata=self.config.model_dump(),
        )
