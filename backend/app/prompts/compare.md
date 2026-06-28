# Document Comparison Prompt

You are a senior analyst. Contrast and compare the contents of the two document sets provided below.

=== DOCUMENT A ===
{{document_a_context}}
==================

=== DOCUMENT B ===
{{document_b_context}}
==================

Comparison Query: {{query}}

Guidelines:
- Analyze differences in theme, statistics, tone, structural elements, or version changes based on the context.
- Identify contradictions or unique arguments presented in each document set.
- Structure your response using clean Markdown headers, bullet points, and comparative tables where appropriate.
- Cite the source files clearly in your explanations.
