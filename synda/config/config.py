from pathlib import Path

import yaml
from pydantic import BaseModel, ValidationError, model_validator
from sqlmodel import Session, select

from synda.config.ablation import Ablation
from synda.config.clean import Clean
from synda.config.generation import Generation
from synda.config.input import InputConfig
from synda.config.metadata import Metadata
from synda.config.output import OutputConfig
from synda.config.split import Split
from synda.database import engine
from synda.model.provider import Provider


class MissingProviderError(Exception):
    pass


class Config(BaseModel):
    input: InputConfig
    pipeline: list[Split | Generation | Ablation | Clean | Metadata]
    output: OutputConfig

    @classmethod
    def from_yaml(cls, path: Path) -> "Config":
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            return cls.model_validate(data)
        except (yaml.YAMLError, ValidationError) as e:
            raise ValueError(f"Error loading configuration: {e}")

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
