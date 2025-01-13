from nebula.config.parser import Step


class Ablation(Step):
    type: str = "ablation"

    def validate_config(self):
        pass

    def get_executor(self):
        pass
