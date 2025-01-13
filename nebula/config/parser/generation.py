from nebula.config.parser import Step


class Generation(Step):
    type: str = "generation"

    def validate_config(self) -> bool:
        return True

    def get_executor(self):
        pass
