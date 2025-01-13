from nebula.pipeline.pipeline_context import PipelineContext


class Chunk:
    def __call__(self, pipeline_context: PipelineContext):
        return "bla"
