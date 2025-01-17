from typing import TYPE_CHECKING

from synda.pipeline.pipeline_context import PipelineContext
from synda.utils import is_debug_enabled

if TYPE_CHECKING:
    from synda.config import Config


class Pipeline:
    def __init__(self, config: "Config"):
        self.config = config
        self.input_loader = config.input.get_loader()
        self.output_saver = config.output.get_saver()
        self.pipeline = config.pipeline
        self.pipeline_context: PipelineContext = PipelineContext()

    def execute(self):
        self.input_loader.load(self.pipeline_context)

        for parser in self.pipeline:
            if is_debug_enabled():
                print(parser)
            executor = parser.get_executor()
            executor.execute(self.pipeline_context)

        self.output_saver.save(self.pipeline_context)
