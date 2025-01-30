import sys
import yaml
from pathlib import Path

import typer
from pydantic import BaseModel, model_validator
from sqlmodel import Session, select

from synda.config.input import Input
from synda.config.output import Output
from synda.config.ablation import Ablation
from synda.config.generation import Generation
from synda.config.split import Split
from synda.config.clean import Deduplicate
from synda.database import engine
from synda.model.provider import Provider


class MissingProviderError(Exception):
    pass


class Config(BaseModel):
    input: Input
    pipeline: list[Split | Generation | Ablation | Deduplicate]
    output: Output

    @staticmethod
    def load_config(config_path: Path) -> "Config":
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
                "Please add them using 'synda provider add <name> --api-key <key>'",
                fg=typer.colors.RED,
            )
            raise typer.Exit(1)

    @model_validator(mode="after")
    def validate_providers(self) -> "Config":
        required_providers = set()
        for step in self.pipeline:
            if isinstance(step, (Generation, Ablation)):
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
