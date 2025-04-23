import itertools
from typing import List
from sqlmodel import Session
from synda.model.run import Run
from synda.pipeline.executor import Executor
from synda.model.node import Node
from synda.progress_manager import ProgressManager
from synda.model.step import Step
from synda.utils.llm_provider import LLMProvider
from synda.model.provider import Provider
from sklearn.metrics.pairwise import cosine_similarity

class DeduplicateEmbed(Executor):
    def __init__(self, session: Session, run: Run, step_model: Step):
        super().__init__(session, run, step_model)
        self.progress = ProgressManager("CLEAN")
        self.provider = Provider.get(self.config.parameters.provider)
        self.model = self.config.parameters.model
        self.api_key = self.provider.api_key
        self.api_url = self.provider.api_url

    def execute(self, pending_nodes: List[Node], processed_nodes: List[Node]) -> List[Node]:
        similarity_threshold = self.config.parameters.similarity_threshold
        texts = [node.value for node in pending_nodes]
        embeddings = LLMProvider.embedding(
            provider=self.provider.name,
            model=self.model,
            api_key=self.api_key,
            texts=texts,
            url=self.api_url,
        )
        result_nodes = self._remove_embed_duplicates(pending_nodes, embeddings, similarity_threshold)
        return [Node(parent_node_id=node.id, value=node.value) for node in result_nodes]

    @staticmethod
    def _remove_embed_duplicates(
        pending_nodes: List[Node], embeddings: List[list], similarity_threshold: float
    ) -> List[Node]:
        keep_indices = set(range(len(pending_nodes)))
        similarity_matrix = cosine_similarity(embeddings)
        for i in range(len(pending_nodes)):
            if i not in keep_indices:
                continue
            for j in range(i + 1, len(pending_nodes)):
                if j not in keep_indices:
                    continue
                sim = similarity_matrix[i, j]
                if sim > similarity_threshold:
                    keep_indices.discard(j)
        return [pending_nodes[i] for i in sorted(keep_indices)] 