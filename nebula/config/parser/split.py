from nebula.config.parser import Step
from nebula.pipeline.executor import Executor


class Split(Step):
    type: str = "split"
    method: str
    parameters: dict

    def validate_config(self) -> bool:
        return True

    def get_executor(self) -> Executor:
        if self.method == "chunk":
            from nebula.pipeline.split import Chunk
            return Chunk(self)
