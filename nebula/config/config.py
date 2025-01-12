import sys
import yaml

from pydantic import BaseModel

from nebula.config.source import Source

from nebula.config.step.ablation import Ablation
from nebula.config.step.generation import Generation
from nebula.config.step.split import Split


class Config(BaseModel):
    source: Source
    pipeline: list[Split | Generation | Ablation]

    @staticmethod
    def load_config(config_path: str) -> "Config":
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return Config.model_validate(yaml.safe_load(file))
        except yaml.YAMLError as e:
            print(f"Error in YAML file: {e}")
            sys.exit(1)
        except FileNotFoundError:
            print(f"The file {config_path} doesn't exist")
            sys.exit(1)
        except ValueError as e:
            print(f"Configuration validation error: {e}")
            sys.exit(1)
