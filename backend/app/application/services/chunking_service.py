from typing import List

class ChunkingService:
    """
    Service responsible for splitting parsed document text into chunks.
    Uses a custom recursive character text splitting algorithm.
    """
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> List[str]:
        """
        Splits text recursively by separators: paragraph (\n\n), line (\n), space ( ), and char.
        Enforces maximum chunk size and handles overlaps.
        """
        if not text:
            return []

        separators = ["\n\n", "\n", " ", ""]
        return self._recursive_split(text, separators, self.chunk_size, self.chunk_overlap)

    def _recursive_split(self, text: str, separators: List[str], max_size: int, overlap: int) -> List[str]:
        # If text is small enough, return it as a single chunk
        if len(text) <= max_size:
            return [text]

        # Select separator
        separator = separators[0] if separators else ""
        next_separators = separators[1:] if len(separators) > 1 else []

        if separator:
            splits = text.split(separator)
        else:
            # Character splitting
            splits = list(text)

        chunks: List[str] = []
        current_chunk = ""

        for part in splits:
            # Re-insert the separator if it's not empty
            part_str = part + separator if separator else part
            
            # If the single part exceeds max_size, we must split it recursively using next separator
            if len(part_str) > max_size:
                # Flush the current chunk first
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                # Recursively split the long part
                sub_chunks = self._recursive_split(part_str, next_separators, max_size, overlap)
                chunks.extend(sub_chunks)
            else:
                # Can we fit this part into the current chunk?
                if len(current_chunk) + len(part_str) <= max_size:
                    current_chunk += part_str
                else:
                    # Flush current chunk
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    # Initialize new chunk with overlap from previous chunk
                    current_chunk = self._get_overlap_text(current_chunk, overlap) + part_str

        # Flush final chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        return [c for c in chunks if c]

    def _get_overlap_text(self, prev_chunk: str, overlap_size: int) -> str:
        if not prev_chunk or overlap_size <= 0:
            return ""
        # Simply take the last N characters of the previous chunk
        if len(prev_chunk) <= overlap_size:
            return prev_chunk
        return prev_chunk[-overlap_size:]
