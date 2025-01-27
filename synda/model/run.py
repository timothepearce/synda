from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlmodel import Column, Relationship, SQLModel, Session, Field, JSON

from synda.database import engine
from synda.model.step import Step, StepStatus

if TYPE_CHECKING:
    from synda.config import Config


class RunStatus(str, Enum):
    RUNNING = "running"
    FINISHED = "finished"
    ERRORED = "errored"


class Run(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    status: RunStatus = Field(default=RunStatus.RUNNING, index=True)
    config: "Config" = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.now)

    steps: list[Step] = Relationship(back_populates="run")

    @staticmethod
    def create_with_steps(session: Session, config: "Config") -> "Run":
        run = Run(config=config.model_dump())

        session.add(run)
        session.flush()

        steps = [
            Step(
                run_id=run.id,
                position=position,
                step_type=pipeline_step.type,
                step_method=pipeline_step.method,
                step_name=pipeline_step.name,
                step_config=pipeline_step.model_dump(),
                status=StepStatus.PENDING,
                run_at=datetime.now(),
            )
            for position, pipeline_step in enumerate(config.pipeline, start=1)
        ]

        session.add_all(steps)
        session.commit()
        session.refresh(run, ["steps"])

        return run

    def update(self, session: Session, status: RunStatus) -> "Run":
        self.status = status

        session.add(self)
        session.commit()
        session.refresh(self)
        return self

    def get_config(self) -> "Config":
        return Config.model_validate(self.config)
