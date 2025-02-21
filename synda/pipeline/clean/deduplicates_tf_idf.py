from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlmodel import Session

from synda.model.run import Run
from synda.pipeline.executor import Executor
from synda.model.node import Node
from synda.progress_manager import ProgressManager
from synda.model.step import Step


class DeduplicateTFIDF(Executor):
    def __init__(self, session: Session, run: Run, step_model: Step):
        super().__init__(session, run, step_model)
        self.progress = ProgressManager("CLEAN")

    def execute(self, input_data: list[Node]) -> list[Node]:
        strategy = self.config.parameters.strategy
        similarity_threshold = self.config.parameters.similarity_threshold
        keep = self.config.parameters.keep

        with self.progress.task("  Cleaning...", len(input_data)) as advance:
            if strategy == "exact":
                result_nodes = self._remove_exact_duplicates(input_data, keep, advance)
            elif strategy == "fuzzy":
                result_nodes = self._remove_fuzzy_duplicates(
                    input_data, similarity_threshold, keep, advance
                )

        return [Node(parent_node_id=node.id, value=node.value) for node in result_nodes]

    @staticmethod
    def _remove_exact_duplicates(
        input_data: list[Node], keep: str, advance
    ) -> list[Node]:
        seen_values = set()
        result = []

        if keep == "first":
            for node in input_data:
                if node.value not in seen_values:
                    seen_values.add(node.value)
                    result.append(node)
                advance()
        elif keep == "last":
            for node in reversed(input_data):
                if node.value not in seen_values:
                    seen_values.add(node.value)
                    result.insert(0, node)
                advance()

        return result

    @staticmethod
    def _remove_fuzzy_duplicates(
        input_data: list[Node], similarity_threshold: float, keep: str, advance
    ) -> list[Node]:
        node_values = [node.value for node in input_data]

        vectorizer = TfidfVectorizer(strip_accents="unicode")
        tfidf_matrix = vectorizer.fit_transform(node_values)
        similarity_matrix = cosine_similarity(tfidf_matrix)
        index_node_to_keep = set(range(len(node_values)))

        for node_index in range(len(node_values)):
            if node_index not in index_node_to_keep:
                advance()
                continue

            for compared_node_index in range(node_index + 1, len(node_values)):
                if compared_node_index not in index_node_to_keep:
                    continue
                if (
                    similarity_matrix[node_index, compared_node_index]
                    > similarity_threshold
                ):
                    if keep == "first":
                        index_node_to_keep.discard(compared_node_index)
                    elif keep == "last":
                        index_node_to_keep.discard(node_index)
                        break

            advance()

        return [input_data[i] for i in sorted(index_node_to_keep)]
