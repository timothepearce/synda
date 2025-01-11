from nebula import Config


class Pipeline:
    def __init__(self, config: Config):
        self.config = config

    def execute(self):
        print(self.config.source.properties)
