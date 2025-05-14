from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlmodel import JSON, Column, Field, Relationship, Session, select

from synda.model.node import Node
from synda.model.step import Step, StepStatus
from synda.model.utils import SQLModel


if TYPE_CHECKING:
    from synda.config import Config


class RunStatus(str, Enum):
    RUNNING = "running"
    FINISHED = "finished"
    STOPPED = "stopped"
    ERRORED = "errored"

DumpedConfig = dict[str, Any]


class Run(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    status: RunStatus = Field(default=RunStatus.RUNNING, index=True)
    config: DumpedConfig = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.now)

    steps: list[Step] = Relationship(back_populates="run")

    @staticmethod
    def get_from_step(session: Session, step: Step) -> "Run":
        return session.exec(select(Run).where(Run.id == step.run_id)).first()

    @staticmethod
    def create_with_steps(session: Session, config: "Config") -> "Run":
        run = Run(config=config.model_dump(mode="json"))

        session.add(run)
        session.flush()

        steps = [
            Step(
                run_id=run.id,
                position=position,
                type=pipeline_step.type,
                method=pipeline_step.method,
                name=pipeline_step.name,
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

    @staticmethod
    def restart_from_step(
        session: Session, step: "Step"
    ) -> tuple["Run", list[Node], list[Step]]:
        run = Run.get_from_step(session, step)
        run.update(session, RunStatus.RUNNING)
        input_nodes = Node.get_input_nodes_from_step(session, step)
        return run, input_nodes, run.steps[step.position - 1 :]

    def update(self, session: Session, status: RunStatus) -> "Run":
        self.status = status

        session.add(self)
        session.commit()
        session.refresh(self)
        return self

    def get_config(self) -> "Config":
        return Config.model_validate(self.config)
