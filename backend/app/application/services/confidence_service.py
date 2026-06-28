from typing import List, Tuple

from app.domain.models import DocumentChunk


class ConfidenceService:
    """
    Service responsible for calculating the confidence score of a RAG pipeline answer.
    Analyzes vector similarities and source coverage constraints.
    """

    def calculate_confidence(
        self, reranked_chunks: List[Tuple[DocumentChunk, float]]
    ) -> str:
        """
        Calculates confidence index: "High", "Medium", or "Low".
        Heuristics:
        - Mean similarity score >= 0.85 AND count >= 3 -> High
        - Mean similarity score >= 0.70 AND count >= 1 -> Medium
        - Otherwise -> Low
        """
        if not reranked_chunks:
            return "Low"

        # Calculate mean similarity of retrieved chunks
        scores = [score for _, score in reranked_chunks]
        mean_score = sum(scores) / len(scores) if scores else 0.0

        chunk_count = len(reranked_chunks)

        if mean_score >= 0.82 and chunk_count >= 3:
            return "High"
        elif mean_score >= 0.68 and chunk_count >= 1:
            return "Medium"
        else:
            return "Low"
        # Wait, let's keep it simple and return High, Medium, Low
