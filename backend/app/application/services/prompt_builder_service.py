import os
from typing import Any, Dict

from app.core.exceptions import PromptBuildError


class PromptBuilderService:
    """
    Service responsible for loading external prompt templates
    and dynamically formatting them with context placeholders.
    """

    def __init__(self):
        # Resolve prompts path relative to project app root
        self.prompts_dir = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            "prompts",
        )

    def _load_template(self, template_name: str) -> str:
        """Reads template contents from files on disk."""
        path = os.path.join(self.prompts_dir, template_name)
        if not os.path.exists(path):
            raise PromptBuildError(f"Required prompt template not found at: {path}")
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            raise PromptBuildError(f"Failed to read prompt template: {str(e)}") from e

    def build_prompt(self, template_name: str, placeholders: Dict[str, Any]) -> str:
        """
        Loads prompt template and replaces custom placeholders matching {{key}} keys.
        """
        template = self._load_template(template_name)

        try:
            formatted = template
            for key, value in placeholders.items():
                target = f"{{{{{key}}}}}"  # Format matching {{key}}
                formatted = formatted.replace(target, str(value))
            return formatted
        except Exception as e:
            raise PromptBuildError(f"Failed formatting prompt placeholders: {str(e)}") from e
