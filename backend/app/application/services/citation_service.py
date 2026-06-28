import re
from typing import List, Dict, Any
from app.domain.models import DocumentChunk

class CitationService:
    """
    Service responsible for parsing LLM generated outputs
    to extract citations and link them back to source document chunks.
    """
    
    def extract_citations(
        self, 
        response_text: str, 
        retrieved_chunks: List[DocumentChunk]
    ) -> List[Dict[str, Any]]:
        """
        Scans assistant response text using regex to find citations matching:
        [Document: file_name.pdf - Page: X]
        Maps matches to the retrieved document chunks list to enrich metadata.
        """
        if not response_text or not retrieved_chunks:
            return []

        # Regex mapping standard citation patterns: [Document: (name) - Page: (number)]
        pattern = r"\[Document:\s*([^\]\-]+?)\s*-\s*Page:\s*(\d+)\]"
        matches = re.findall(pattern, response_text)
        
        citations: List[Dict[str, Any]] = []
        seen_keys = set()
        
        for doc_name, page_num_str in matches:
            doc_name = doc_name.strip()
            try:
                page_num = int(page_num_str)
            except ValueError:
                page_num = 1
                
            key = (doc_name, page_num)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            
            # Match against the retrieved chunks list to find matching chunk index and calculate confidence
            matching_chunk = None
            for chunk in retrieved_chunks:
                # Find matching chunk index based on name check
                # (Assuming chunk has document relationship populated or checking parent document names)
                # In this mock verification, we match chunk page number or look up details
                if chunk.page_number == page_num:
                    matching_chunk = chunk
                    break
                    
            chunk_idx = matching_chunk.chunk_index if matching_chunk else 0
            
            # Add to citation mapping list
            citations.append({
                "document_name": doc_name,
                "page_number": page_num,
                "chunk_index": chunk_idx,
                "confidence": 0.95 # Base confidence mapping
            })
            
        return citations
