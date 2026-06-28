import json
import time
import uuid
from typing import Generator, Dict, Any, List
import google.generativeai as genai
from sqlalchemy.orm import Session as SqlSession

from app.core.config import settings
from app.core.exceptions import AIProviderError, StreamingError
from app.domain.models import AIUsageLog, Message
from app.domain.repositories.usage_log_repository import IUsageLogRepository
from app.application.services.query_rewrite_service import QueryRewriteService
from app.application.services.retrieval_service import RetrievalService
from app.application.services.prompt_builder_service import PromptBuilderService
from app.application.services.conversation_memory_service import (
    ConversationMemoryService,
)
from app.application.services.citation_service import CitationService
from app.application.services.confidence_service import ConfidenceService
from app.core.logging import logger


class ChatService:
    """
    Master RAG controller coordinating query preprocessing, hybrid retrieval, prompt framing,
    Gemini token completions streaming (SSE), citations generation, confidence assessments,
    and usage logs.
    """

    def __init__(
        self,
        db: SqlSession,
        usage_log_repo: IUsageLogRepository,
        query_rewrite_service: QueryRewriteService,
        retrieval_service: RetrievalService,
        prompt_builder_service: PromptBuilderService,
        memory_service: ConversationMemoryService,
        citation_service: CitationService,
        confidence_service: ConfidenceService,
    ):
        self.db = db
        self.usage_log_repo = usage_log_repo
        self.query_rewrite_service = query_rewrite_service
        self.retrieval_service = retrieval_service
        self.prompt_builder_service = prompt_builder_service
        self.memory_service = memory_service
        self.citation_service = citation_service
        self.confidence_service = confidence_service

    def _estimate_cost(
        self, model_name: str, input_tokens: int, output_tokens: int
    ) -> float:
        """Calculates estimated Google Gemini API execution cost."""
        if "pro" in model_name.lower():
            # Gemini 1.5 Pro standard rates
            input_rate = 1.25 / 1_000_000
            output_rate = 5.00 / 1_000_000
        else:
            # Gemini 1.5 Flash rates
            input_rate = 0.075 / 1_000_000
            output_rate = 0.30 / 1_000_000
        return (input_tokens * input_rate) + (output_tokens * output_rate)

    def stream_chat(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        collection_id: uuid.UUID,
        user_query: str,
        preferred_model: str = "gemini-1.5-flash",
        temperature: float = 0.20,
    ) -> Generator[str, None, None]:
        """
        Executes query rewrite, hybrid retrieval, formats prompt templates,
        streams token answers, extracts citations, runs confidence scoring,
        and saves logs. Yields Server-Sent Events (SSE).
        """
        request_id = uuid.uuid4()
        start_time_ms = int(time.time() * 1000)

        # 1. Retrieve and format conversation memory context
        conversation_history_str = self.memory_service.get_history_as_string(
            conversation_id, max_messages=8
        )

        # 2. Rewrite query (resolving pronouns)
        rewritten_query = self.query_rewrite_service.rewrite_query(
            user_query, conversation_history_str
        )
        logger.info(f"Query rewritten: '{user_query}' -> '{rewritten_query}'")

        # 3. Hybrid search documents retrieval
        try:
            retrieved_chunks = self.retrieval_service.retrieve_context(
                collection_id=collection_id, query=rewritten_query, limit=5
            )
        except Exception as e:
            # Fallback if no context found, log warning and set empty context
            logger.warning(f"RAG retrieval resolved zero chunks: {str(e)}")
            retrieved_chunks = []

        # 4. Construct context string for Prompt Builder
        context_parts = []
        for chunk, score in retrieved_chunks:
            # Extract document metadata if available
            doc_name = getattr(chunk, "document_name", f"Document-{chunk.document_id}")
            context_parts.append(
                f"[Document: {doc_name} - Page: {chunk.page_number or 1}] (Relevance Score: {score:.2f})\n"
                f"{chunk.content}"
            )
        context_str = (
            "\n\n---\n\n".join(context_parts)
            if context_parts
            else "No document context available."
        )

        # 5. Build prompt
        placeholders = {
            "context": context_str,
            "conversation": conversation_history_str,
            "question": rewritten_query,
        }
        formatted_prompt = self.prompt_builder_service.build_prompt(
            "chat.md", placeholders
        )

        # 6. Stream content from Gemini API
        if not settings.GEMINI_API_KEY:
            raise AIProviderError("Gemini API key is not configured.")

        # Save user query to history
        self.memory_service.add_message(conversation_id, "user", user_query)
        self.db.commit()  # Flush use-case database transition boundaries

        model = genai.GenerativeModel(preferred_model)

        # Calculate prompt token counts
        try:
            prompt_tokens = model.count_tokens(formatted_prompt).total_tokens
        except Exception:
            prompt_tokens = len(formatted_prompt) // 4  # Rough token backup estimate

        full_response_text = ""

        try:
            response_stream = model.generate_content(
                contents=formatted_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                ),
                stream=True,
            )

            # Stream tokens to client
            for response_chunk in response_stream:
                token_text = response_chunk.text
                full_response_text += token_text
                # SSE message format
                yield f"data: {json.dumps({'text': token_text})}\n\n"

        except Exception as e:
            logger.error(f"Streaming failed: {str(e)}")
            yield f"data: {json.dumps({'error': 'Streaming interrupted due to model failure.'})}\n\n"
            return

        # 7. Post-Generation: Citations parsing and Confidence estimation
        pure_chunks_list = [chunk for chunk, _ in retrieved_chunks]
        citations = self.citation_service.extract_citations(
            full_response_text, pure_chunks_list
        )
        confidence = self.confidence_service.calculate_confidence(retrieved_chunks)

        # 8. Save assistant response to history
        self.memory_service.add_message(
            conversation_id, "assistant", full_response_text, citations
        )

        # 9. Token usage analysis
        try:
            completion_tokens = model.count_tokens(full_response_text).total_tokens
        except Exception:
            completion_tokens = len(full_response_text) // 4

        total_tokens = prompt_tokens + completion_tokens
        duration_ms = int(time.time() * 1000) - start_time_ms
        estimated_cost = self._estimate_cost(
            preferred_model, prompt_tokens, completion_tokens
        )

        # 10. Record AI Usage analytics
        usage_log = AIUsageLog(
            id=uuid.uuid4(),
            user_id=user_id,
            request_id=request_id,
            model=preferred_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
            response_time_ms=duration_ms,
            status="SUCCESS",
            timestamp=datetime.utcnow(),
        )
        self.usage_log_repo.add(usage_log)
        self.db.commit()

        # Final SSE packet returning citations and metrics
        final_metadata = {
            "citations": citations,
            "confidence": confidence,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "estimated_cost": float(estimated_cost),
                "duration_ms": duration_ms,
            },
        }
        yield f"data: {json.dumps(final_metadata)}\n\n"
