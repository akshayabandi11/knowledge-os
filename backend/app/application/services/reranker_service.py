import re
from typing import List, Tuple
from app.domain.models import DocumentChunk

class RerankerService:
    """
    Service responsible for post-retrieval reranking.
    Applies heuristics-based scoring combining semantic similarity, Jaccard keyword overlap,
    and document positioning boosts to return the highest-quality context.
    """
    
    def rerank(
        self, 
        query: str, 
        chunks: List[Tuple[DocumentChunk, float]], 
        limit: int = 5
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Reranks fused document chunks using heuristic scores:
        Score = (Semantic_Score * 0.6) + (Jaccard_Overlap * 0.3) + (Position_Boost * 0.1)
        """
        if not chunks:
            return []

        # Tokenize query for overlap calculations
        query_words = set(re.findall(r"\w+", query.lower()))
        
        reranked_list: List[Tuple[DocumentChunk, float]] = []

        for chunk, fused_score in chunks:
            # 1. Base semantic score (we use the normalized fused score or local text checking)
            semantic_score = fused_score
            
            # 2. Calculate Jaccard keyword overlap
            chunk_words = set(re.findall(r"\w+", chunk.content.lower()))
            intersection = query_words.intersection(chunk_words)
            union = query_words.union(chunk_words)
            jaccard_score = len(intersection) / len(union) if union else 0.0
            
            # 3. Position Boost (prioritize introduction/early pages in document)
            # Chunks at index 0 or page 1 get a microscopic boost (up to 0.05)
            position_boost = 0.05 if chunk.chunk_index == 0 else 0.0
            if chunk.page_number and chunk.page_number == 1:
                position_boost += 0.05

            # 4. Calculate final composite score
            composite_score = (semantic_score * 0.6) + (jaccard_score * 0.3) + position_boost
            
            reranked_list.append((chunk, composite_score))

        # Sort by composite score in descending order
        reranked_list.sort(key=lambda x: x[1], reverse=True)
        
        return reranked_list[:limit]
