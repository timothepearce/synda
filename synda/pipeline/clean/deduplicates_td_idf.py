from typing import List
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlmodel import Session

from synda.pipeline.executor import Executor
from synda.model.node import Node
from synda.progress_manager import ProgressManager
from synda.model.step import Step

class DeduplicateTFIDF(Executor):    
    def __init__(self, session: Session, step_model: Step):
        super().__init__(session, step_model)
        self.progress = ProgressManager("CLEAN")

    def execute(self, input_data: List[Node]) -> List[Node]:
        strategy = self.config.parameters.strategy
        similarity_threshold = self.config.parameters.similarity_threshold
        keep = self.config.parameters.keep
        
        with self.progress.task("Removing duplicates...", len(input_data)) as advance:
            # Convert nodes to list of values
            data_list = [str(node.value) for node in input_data]
            
            if strategy == "exact":
                result_list = self._remove_exact_duplicates(data_list, keep, advance)
            elif strategy == "fuzzy":
                result_list = self._remove_fuzzy_duplicates(data_list, similarity_threshold, keep, advance)
                
            advance()
        # Convert back to Node objects
        return [Node(value=item) for item in result_list]

    def _remove_exact_duplicates(self, data: List[str], keep: str, advance) -> List[str]:
        seen_values = set()
        result = []
        
        if keep == "first":
            for item in data:
                if item not in seen_values:
                    seen_values.add(item)
                    result.append(item)
                advance()
        elif keep == "last":
            for item in reversed(data):
                if item not in seen_values:
                    seen_values.add(item)
                    result.insert(0, item)
                advance()
                    
        return result

    def _remove_fuzzy_duplicates(self, data: List[str], similarity_threshold: float, keep: str, advance) -> List[str]:
        vectorizer = TfidfVectorizer(strip_accents='unicode')
        tfidf_matrix = vectorizer.fit_transform(data)
        similarity_matrix = cosine_similarity(tfidf_matrix)
        to_keep = set(range(len(data)))
        
        for i in range(len(data)):
            if i not in to_keep:
                continue
            for j in range(i + 1, len(data)):
                if j not in to_keep:
                    continue
                if similarity_matrix[i, j] > similarity_threshold:
                    if keep == "first":
                        to_keep.discard(j)
                    elif keep == "last":
                        to_keep.discard(i)
                        break
            advance()
        
        return [data[i] for i in sorted(to_keep)]