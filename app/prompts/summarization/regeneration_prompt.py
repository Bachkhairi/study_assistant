def build_prompt(initial_summary: str, critique: str) -> str:
    return f"""
You are a helpful study assistant.

Your task is to revise the Student's Summary

You are revising a student's new summary block using constructive feedback from a thoughtful evaluator. This summary is part of a longer markdown-based knowledge document.

**Original Summary Block (to revise):**
{initial_summary}

**Critique (from evaluator):**
{critique}

**Instructions for the revised summary:**

- Maintain the same content but improve structure and clarity based on the critique.
- Use markdown formatting correctly:
  - Use `#` for main sections, `##` for sub-sections, and `###` for sub-sub-sections.
  - **Do not** add spaces between `#` characters (avoid `## #` as it breaks formatting in Notion).
  - Use `-` for bullet points (not `•`).
  - Use **bold** for key terms.  
- Add emojis naturally for headings and sections:
  - Choose an emoji that matches the *theme or tone* of the section (e.g., 🌍 for global topics, 📊 for data, 🛠️ for methods, ⚠️ for warnings, 🌟 for highlights).
  - You can pick from this broad set: 🌍, 🌱, 🔥, ⚡, 💡, 📌, ✅, ⚠️, 🚀, 🎯, 📝, 📖, 🧠, 💻, 📊, 🏆, 🔍, 🔑, 🏗️, 🛠️, 🎓, 🧩, 🔬, ⏳, 📅, 🏞️, 🌐, 🏛️, 🏥, 🏢, 🏠, 🔒, 📈, 📉, 🛡️, ❤️, 🔄, 🌟, 🎉, ✨.
  - Do **not** use the same emoji repeatedly unless it makes sense.
  - Do not add emojis to every bullet point—use them mainly for section headings or special emphasis.
- You have full freedom to restructure the summary to best convey its meaning and flow. Avoid static templates; vary structure if it makes the summary clearer.
- Begin with a short introductory sentence if suggested by the critique.
- Avoid unnecessary repetition.
- Do **not** include the critique in the final output.

---

### Output Format

Return a single string containing the revised markdown summary between `<<FINAL_SUMMARY>>` delimiters.

**Example**:
<<FINAL_SUMMARY>>
<<content>>
<<FINAL_SUMMARY>>


""".strip()

