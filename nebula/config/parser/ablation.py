from nebula.config.parser import Step


class Ablation(Step):
    type: str = "ablation"

    def get_executor(self):
        pass
