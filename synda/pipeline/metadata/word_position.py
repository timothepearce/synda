import re
import unicodedata

from sqlmodel import Session

from synda.model.run import Run
from synda.pipeline.executor import Executor
from synda.model.node import Node
from synda.progress_manager import ProgressManager
from synda.model.step import Step
from synda.utils.prompt_builder import PromptBuilder


class WordPosition(Executor):
    def __init__(self, session: Session, run: Run, step_model: Step):
        super().__init__(session, run, step_model)
        self.progress = ProgressManager("METADATA")

    def execute(self, input_data: list[Node]):
        result = []
        matches = self.config.parameters.matches

        with self.progress.task("  Metadata...", len(input_data)) as advance:
            for node in input_data:
                metadata = []
                text = node.value

                for label, pattern in matches.items():
                    pattern = PromptBuilder.build(self.session, pattern, [node])
                    regex_pattern = self._create_pattern_ignoring_case_and_accents(
                        pattern
                    )
                    match = re.search(regex_pattern, text)

                    if match:
                        metadata_entry = {
                            "label": label,
                            "start": match.start(),
                            "end": match.end(),
                            "value": match.group(),
                        }
                        metadata.append(metadata_entry)

                result.append(
                    Node(
                        parent_node_id=node.id, value=node.value, node_metadata=metadata
                    )
                )
                advance()

        return result

    @staticmethod
    def _create_pattern_ignoring_case_and_accents(pattern: str) -> str:
        pattern = pattern.lower()
        pattern = unicodedata.normalize("NFKD", pattern)
        pattern = "".join(c for c in pattern if ord(c) < 128)
        pattern = re.escape(pattern)
        return f"(?i){pattern}"
