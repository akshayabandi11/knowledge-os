from typing import List, Tuple, Dict, Any
from uuid import UUID
from app.domain.models import DocumentChunk

class FusionService:
    """
    Service implementing Reciprocal Rank Fusion (RRF) to merge multiple ranked retrieval lists
    (Vector Search and Keyword Search) into a single unified ranked result list.
    """
    def __init__(self, k: int = 60):
        # k is the constant scale factor (standard RRF parameter)
        self.k = k

    def fuse_results(
        self, 
        vector_results: List[Tuple[DocumentChunk, float]], 
        keyword_results: List[Tuple[DocumentChunk, float]]
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Merges vector and keyword search results using Reciprocal Rank Fusion.
        Returns a single unified list of chunks ordered by their fused RRF score.
        """
        rrf_scores: Dict[UUID, float] = {}
        chunk_map: Dict[UUID, DocumentChunk] = {}

        # 1. Process Vector Search Results (ranked 1 to N)
        for rank, (chunk, _) in enumerate(vector_results, start=1):
            chunk_id = chunk.id
            chunk_map[chunk_id] = chunk
            
            # RRF score addition: 1 / (k + rank)
            score = 1.0 / (self.k + rank)
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + score

        # 2. Process Keyword Search Results (ranked 1 to N)
        for rank, (chunk, _) in enumerate(keyword_results, start=1):
            chunk_id = chunk.id
            chunk_map[chunk_id] = chunk
            
            score = 1.0 / (self.k + rank)
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + score

        # 3. Sort chunks based on RRF scores in descending order
        sorted_keys = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        
        # Return chunks and their computed RRF scores
        return [(chunk_map[key], rrf_scores[key]) for key in sorted_keys]
