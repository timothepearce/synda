import sys
import yaml
import io
from pathlib import Path
from typing import List, Dict, Any, Union, Optional

import typer
from pydantic import BaseModel, model_validator
from sqlmodel import Session, select

from synda.config.input import Input
from synda.config.output import Output
from synda.config.ablation import Ablation
from synda.config.generation import Generation
from synda.config.split import Split
from synda.config.clean import Clean
from synda.config.metadata import Metadata
from synda.config.step import Step
from synda.database import engine
from synda.model.provider import Provider


class MissingProviderError(Exception):
    pass


class Config(BaseModel):
    input: Input
    pipeline: List[Step]
    output: Output

    @staticmethod
    def load_config(config_path: Path) -> "Config":
        """Load configuration from a file."""
        try:
            with open(config_path, "r", encoding="utf-8") as file:
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
        except MissingProviderError as e:
            typer.secho(
                f"The following providers are not configured: {str(e)}.\n"
                "Please add them using 'synda provider add <n> --api-key <key>'",
                fg=typer.colors.RED,
            )
            raise typer.Exit(1)
    
    @staticmethod
    def load_config_from_string(config_yaml: str) -> "Config":
        """Load configuration from a YAML string."""
        try:
            return Config.model_validate(yaml.safe_load(config_yaml))
        except yaml.YAMLError as e:
            print(f"Error in YAML string: {e}")
            sys.exit(1)
        except ValueError as e:
            print(f"Configuration validation error: {e}")
            sys.exit(1)
        except MissingProviderError as e:
            typer.secho(
                f"The following providers are not configured: {str(e)}.\n"
                "Please add them using 'synda provider add <n> --api-key <key>'",
                fg=typer.colors.RED,
            )
            raise typer.Exit(1)
    
    def save_config(self, config_file: Path) -> None:
        """Save configuration to a file."""
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(self.model_dump(), f)
    
    def to_yaml(self) -> str:
        """Convert configuration to a YAML string."""
        return yaml.dump(self.model_dump())
    
    @property
    def has_input_step(self) -> bool:
        """Check if the pipeline has an input step."""
        return any(step.type == "input" for step in self.pipeline)
    
    @property
    def has_output_step(self) -> bool:
        """Check if the pipeline has an output step."""
        return any(step.type == "output" for step in self.pipeline)

    @model_validator(mode="after")
    def validate_providers(self) -> "Config":
        required_providers = set()
        for step in self.pipeline:
            if step.type in ["generation", "ablation"]:
                if hasattr(step.parameters, "provider"):
                    required_providers.add(step.parameters.provider)

        if not required_providers:
            return self

        with Session(engine) as session:
            statement = select(Provider).where(
                Provider.name.in_(required_providers)  # noqa
            )
            existing_providers = {provider.name for provider in session.exec(statement)}

            missing_providers = required_providers - existing_providers
            if missing_providers:
                providers_list = ", ".join(missing_providers)
                raise MissingProviderError(f"{providers_list}")

        return self