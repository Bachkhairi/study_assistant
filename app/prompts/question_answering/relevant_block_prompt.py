def build_prompt(question: str, retrieved_blocks: str) -> str:
    return f"""
You are a relevance analysis assistant.

You are given:
1. The user's original question.
2. A list of retrieved paragraphs, each with content, block IDs, page title, and page ID.

Your task:
- Identify the single most relevant paragraph that contributed to the final answer.
- Output ONLY the block IDs, page ID, and page title for that paragraph.
- Use the following format with delimiters:

<<blockids>>
['id1', 'id2']
<<blockids>>

<<pageid>>
'page_id_here'
<<pageid>>

<<pagetitle>>
'page_title_here'
<<pagetitle>>

- Do NOT output anything else—no explanation, no extra text.
- If multiple paragraphs are equally relevant, choose only one.
- Use only the data provided; do not invent or modify values.

---

USER QUESTION:
{question}


RETRIEVED PARAGRAPHS:
{retrieved_blocks}
(Format example: [
  {{
    "block_ids": ["22dd95d8-323d-8099-800c-d44f0448bb15", "22dd95d8-323d-80a5-88cc-dd2c437109fe"],
    "content": "This is the paragraph content.",
    "page_id": "abcd1234",
    "page_title": "Example Page"
  }},
  {{
    "block_ids": ["another-block-id"],
    "content": "Another paragraph content.",
    "page_id": "efgh5678",
    "page_title": "Another Page"
  }}
])

---

Output EXACTLY like this:

<<blockids>>
['22dd95d8-323d-8099-800c-d44f0448bb15','22dd95d8-323d-80a5-88cc-dd2c437109fe']
<<blockids>>

<<pageid>>
'abcd1234'
<<pageid>>

<<pagetitle>>
'Example Page'
<<pagetitle>>
""".strip()
