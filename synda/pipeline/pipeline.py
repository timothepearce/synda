from typing import TYPE_CHECKING

from synda.model.step import Step, StepStatus
from sqlmodel import Session, select
from sqlalchemy import and_

from synda.database import engine
from synda.model.run import Run, RunStatus
from synda.utils.env import is_debug_enabled

if TYPE_CHECKING:
    from synda.config import Config


class Pipeline:
    def __init__(self, config: "Config"):
        self.config = config
        self.session = Session(engine)
        self.input_loader = config.input.get_loader()
        self.output_saver = config.output.get_saver()
        self.pipeline = config.pipeline

    def execute(self):
        try:
            self.run = Run.create_with_steps(self.session, self.config)
            input_nodes = self.input_loader.load(self.session)

            for step in self.run.steps:
                if is_debug_enabled():
                    print(step)

                executor = step.get_step_config().get_executor(
                    self.session, self.run, step
                )
                input_nodes = executor.execute_and_update_step(input_nodes)

            self.output_saver.save(input_nodes)

            self.run.update(self.session, RunStatus.FINISHED)
        except KeyboardInterrupt:
            try:
                user_input = input(f"\nAre you sure you want to stop the run {self.run.id}? [y/N]: ").strip().lower()
                if user_input == 'y':
                    self.run.update(self.session, RunStatus.STOPPED)
                    print(f"Run with id {self.run.id} is stopped.\n To resume the run, please use")
                    print(f"synda generate --resume --run-id={self.run.id}")
                    exit(0)
                else:
                    print("Continuing execution...\n")
                    self.resume(run_id=self.run.id)
            except KeyboardInterrupt:
                print("\nForce exit detected. Exiting program...")
                exit(1)
        except Exception as e:
            self.run.update(self.session, RunStatus.ERRORED)
            raise e

    def resume(self, run_id: int):
        try:
            print(f"Resuming run {run_id}")
            self.run = self.session.exec(select(Run).where(Run.id == run_id)).first()
            resumed_step: Step = self.session.exec(
                select(Step).where(
                    and_(Step.status != StepStatus.COMPLETED, Step.run_id == run_id)
                ).order_by(Step.position.asc())
            ).first()

            input_nodes, remaining_steps = self.run.resume_from_step(self.session, step=resumed_step)

            for step_ in remaining_steps:
                if is_debug_enabled():
                    print(step_)

                executor = step_.get_step_config().get_executor(
                    self.session, self.run, step_
                )
                input_nodes = executor.execute_and_update_step(input_nodes, restarted=True)
        except Exception as e:
            self.run.update(self.session, RunStatus.ERRORED)
            raise e
