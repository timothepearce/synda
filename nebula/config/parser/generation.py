from nebula.config.parser import Step


class Generation(Step):
    type: str = "generation"

    def get_executor(self):
        pass
