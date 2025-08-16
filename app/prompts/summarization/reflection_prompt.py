def build_prompt(initial_summary: str, retrieved_context: str, heading_tree: str) -> str:
    return f"""
You are a careful evaluator of a long-term knowledge summary.

Over time, a student has been constructing a structured markdown-based summary. Your job is to reflect on the newest addition, and offer constructive feedback to ensure that it fits well into the existing summary.

---

**Existing Summary Structure**
{heading_tree}

**Semantic Context from Prior Content**
{retrieved_context}


**New Summary Block to Evaluate**
{initial_summary}

---

Your tasks:
- Assess flow and consistency with prior parts.
- Suggest structural improvements, if any.
- Identify redundancies, tone shifts, or stylistic mismatches.
- DO NOT rewrite content. Only give constructive critique.
""".strip()
