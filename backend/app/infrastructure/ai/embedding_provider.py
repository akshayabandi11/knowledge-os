import abc
from typing import List
import google.generativeai as genai
from app.core.config import settings
from app.core.exceptions import AIProviderError


class BaseEmbeddingProvider(abc.ABC):
    """
    Abstract Base Class for Vector Embedding Providers.
    Ensures plug-and-play capability for OpenAI, SentenceTransformers, or Gemini.
    """

    @abc.abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """Generates a vector embedding for a query string."""
        pass

    @abc.abstractmethod
    def embed_chunks(self, chunks: List[str]) -> List[List[float]]:
        """Generates vector embeddings for a list of document chunks."""
        pass


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """
    Gemini API implementation of vector embedding generation.
    Utilizes models/text-embedding-004.
    """

    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = "models/text-embedding-004"

    def embed_query(self, query: str) -> List[float]:
        if not settings.GEMINI_API_KEY:
            raise AIProviderError("Gemini API key is not configured.")
        try:
            response = genai.embed_content(
                model=self.model, content=query, task_type="retrieval_query"
            )
            return response["embedding"]
        except Exception as e:
            raise AIProviderError(f"Gemini query embedding failed: {str(e)}")

    def embed_chunks(self, chunks: List[str]) -> List[List[float]]:
        if not settings.GEMINI_API_KEY:
            raise AIProviderError("Gemini API key is not configured.")
        if not chunks:
            return []

        embeddings: List[List[float]] = []
        batch_size = 50

        try:
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i : i + batch_size]
                response = genai.embed_content(
                    model=self.model, content=batch, task_type="retrieval_document"
                )
                embeddings.extend(response["embedding"])
            return embeddings
        except Exception as e:
            raise AIProviderError(f"Gemini batch embedding failed: {str(e)}")
