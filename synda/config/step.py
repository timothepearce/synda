from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Any, Union, Optional

from pydantic import BaseModel, model_validator, Field
from sqlmodel import Session

from synda.model.run import Run
from synda.model.step import Step as StepModel

if TYPE_CHECKING:
    from synda.pipeline.executor import Executor
    from synda.pipeline.async_executor import AsyncExecutor


class StepParameters(BaseModel):
    """Base class for step parameters."""
    pass


class Step(BaseModel):
    """Base class for pipeline steps."""
    type: str
    method: str
    name: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def set_default_name(self) -> "Step":
        """Set a default name if none is provided."""
        if self.name is None:
            self.name = f"{self.type}_{self.method}"
        return self

    def get_executor(self, session: Session, run: Run, step_model: StepModel) -> Union["Executor", "AsyncExecutor"]:
        """Get the appropriate executor for this step."""
        # Import here to avoid circular imports
        from synda.pipeline.executor import Executor
        from synda.pipeline.generation.llm import LLM
        from synda.pipeline.ablation.llm_judge_binary import LLMJudgeBinary
        from synda.pipeline.ablation.async_llm_judge_binary import AsyncLLMJudgeBinary
        from synda.pipeline.split.chunk import Chunk
        from synda.pipeline.split.separator import Separator
        from synda.pipeline.clean.deduplicates_tf_idf import DeduplicatesTfIdf
        from synda.pipeline.metadata.word_position import WordPosition
        from synda.pipeline.input.input_step import InputStep
        from synda.pipeline.output.output_step import OutputStep
        from synda.pipeline.custom.script_step import ScriptStep
        
        # Check if we should use async executors
        use_async = self.parameters.get("use_async", False)
        
        # Map step types and methods to their executor classes
        executor_map = {
            ("generation", "llm"): LLM,
            ("ablation", "llm-judge-binary"): AsyncLLMJudgeBinary if use_async else LLMJudgeBinary,
            ("split", "chunk"): Chunk,
            ("split", "separator"): Separator,
            ("clean", "deduplicate-tf-idf"): DeduplicatesTfIdf,
            ("metadata", "word-position"): WordPosition,
            ("input", "csv"): InputStep,
            ("input", "xls"): InputStep,
            ("output", "csv"): OutputStep,
            ("output", "xls"): OutputStep,
            ("custom", "script"): ScriptStep,
        }
        
        # Get the executor class
        executor_class = executor_map.get((self.type, self.method))
        
        if executor_class:
            return executor_class(session, run, step_model)
        else:
            # Default executor
            return Executor(session, run, step_model)
