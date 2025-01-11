from nebula import Config


class Pipeline:
    def __init__(self, config: Config):
        self.config = config

    def execute(self):
        print(f"Source: {self.config.source.properties.path}")
        print(f"Pipeline: {self.config.pipeline}")
