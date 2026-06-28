import io
import os
from typing import BinaryIO
import pypdf
import google.generativeai as genai
from app.core.config import settings
from app.core.exceptions import ValidationError, AIProviderError


class ParsingService:
    """
    Service responsible for extracting text from different file formats.
    Dynamically loads prompt instructions from disk templates.
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

    def _get_prompt_template(self, filename: str) -> str:
        """Loads prompt content from prompts directory."""
        path = os.path.join(self.prompts_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Required prompt template not found at {path}")
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()

    def parse_txt(self, file_data: BinaryIO) -> str:
        try:
            file_data.seek(0)
            return file_data.read().decode("utf-8")
        except Exception as e:
            raise ValidationError(f"Failed to parse text file: {str(e)}")

    def parse_pdf(self, file_data: BinaryIO) -> str:
        try:
            file_data.seek(0)
            reader = pypdf.PdfReader(file_data)
            text_parts = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    # Enclose page boundaries cleanly for later citation indexing
                    text_parts.append(f"--- PAGE {i + 1} ---\n{page_text}")
            return "\n\n".join(text_parts)
        except Exception as e:
            raise ValidationError(f"Failed to parse PDF file: {str(e)}")

    def parse_image_ocr(self, file_data: BinaryIO, mime_type: str) -> str:
        """
        Sends image bytes directly to Gemini 1.5 Flash to perform multimodal OCR.
        Loads instructions dynamically from disk templates.
        """
        if not settings.GEMINI_API_KEY:
            raise AIProviderError(
                "Gemini API key is not configured. OCR requires Gemini access."
            )

        try:
            file_data.seek(0)
            image_bytes = file_data.read()

            # Load OCR instructions template from disk
            ocr_instruction = self._get_prompt_template("ocr.txt")

            model = genai.GenerativeModel("gemini-1.5-flash")
            contents = [{"mime_type": mime_type, "data": image_bytes}, ocr_instruction]

            response = model.generate_content(contents=contents)
            if not response.text:
                raise AIProviderError(
                    "Gemini model returned empty response for OCR request."
                )
            return response.text
        except Exception as e:
            raise AIProviderError(f"Gemini OCR extraction failed: {str(e)}")

    def parse_file(self, file_data: BinaryIO, file_name: str, file_type: str) -> str:
        ext = file_name.split(".")[-1].lower()

        if ext == "txt":
            return self.parse_txt(file_data)
        elif ext == "pdf":
            return self.parse_pdf(file_data)
        elif ext in ["png", "jpg", "jpeg", "webp"]:
            mime_type = f"image/{ext}" if ext != "jpg" else "image/jpeg"
            return self.parse_image_ocr(file_data, mime_type)
        else:
            raise ValidationError(f"Unsupported file extension: {ext}")
