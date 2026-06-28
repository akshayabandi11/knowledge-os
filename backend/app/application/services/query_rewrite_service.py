import os

import google.generativeai as genai

from app.core.config import settings


class QueryRewriteService:
    """
    Service responsible for query rewriting and pronoun resolution.
    Transforms contextual inputs (e.g. "What are its pros?") into self-contained search queries.
    """

    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
        self.prompts_dir = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            "prompts",
        )

    def _get_template(self) -> str:
        path = os.path.join(self.prompts_dir, "query_rewrite.md")
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()

    def rewrite_query(self, query: str, conversation_history_str: str) -> str:
        """
        Rewrites user question resolving references to past context.
        If history is empty, returns original query immediately.
        """
        if not conversation_history_str.strip():
            return query

        if not settings.GEMINI_API_KEY:
            # Fallback in case of missing keys
            return query

        try:
            template = self._get_template()
            formatted_prompt = template.replace(
                "{{conversation}}", conversation_history_str
            ).replace("{{question}}", query)

            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(
                contents=formatted_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0,  # Strict self-contained output
                    max_output_tokens=150,
                ),
            )
            rewritten = response.text.strip()
            return rewritten if rewritten else query
        except Exception as e:
            # Fallback to original query on failure to ensure system availability
            from app.core.logging import logger

            logger.error(f"Query rewrite failed: {str(e)}. Using original query.")
            return query
