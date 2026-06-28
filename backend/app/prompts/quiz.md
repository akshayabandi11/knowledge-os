# Quiz Generation Prompt

You are an expert educator. Your task is to generate a challenging, educational multiple-choice quiz based ONLY on the document content provided below.

Document Content:
{{context}}

Generate a quiz containing exactly {{count}} questions.
Format your output as a valid JSON array of objects. Do not wrap in markdown blocks, do not add introductory text. Return raw JSON matching this structure:

[
  {
    "question": "The question text?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_option": 0, // index of the correct option (0-indexed)
    "explanation": "Detailed explanation of why this option is correct based on the text."
  }
]
