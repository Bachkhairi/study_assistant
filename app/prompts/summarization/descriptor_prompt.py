def build_prompt(old_descriptor: str, final_summary = "") -> str:
    if not old_descriptor.strip():
        # Initial descriptor generation prompt
        return f"""
You are responsible for creating a compact, high-level descriptor of a large markdown summary for the first time.

The descriptor is a single string. It follows this format:

First line: A brief global summary of the entire summary (short but comprehensive).

Then: A few (3–5 max) bullet points summarizing the main topics and key takeaways.

Bullets should be rewritten or merged if needed to avoid growing linearly.

Each bullet must be short (one phrase or sentence) and describe what the summary is stating overall.

Example:
    Global: Covers climate change causes, effects, and solutions  
    - Explains greenhouse gas emissions and how they drive warming  
    - Highlights major sources like CO2 from fossil fuels and methane from agriculture  
    - Outlines mitigation strategies and potential solutions  


---

**Initial Summary:**
{final_summary}

---

Your task: **Create the initial descriptor** based solely on the final summary.  
Keep it concise and global in nature. Avoid detailed hierarchy; instead, merge topics into broad bullets. 

Output with delimiters:

<<UPDATED_DESCRIPTOR>>
<new descriptor here>
<<UPDATED_DESCRIPTOR>>
""".strip()

    else:
        # Descriptor update prompt
        return f"""
You are responsible for maintaining a compact, high-level descriptor of a large markdown summary.

The descriptor is a single string. It follows this format:

First line: A brief global summary of the entire summary so far (short but comprehensive).

Then: A few (5–20 max) bullet points summarizing the main topics and key takeaways.

Bullets should be rewritten or merged if needed to avoid growing linearly.

Each bullet must be short (one phrase or sentence) and capture the overall scope of the summary.



Global: Covers climate change causes, impacts, mitigation strategies, and global policies
    - Causes of Climate Change: Greenhouse gases from human activities  
    - CO2 Emissions: Major sources include fossil fuels, transportation, and industry  
    - Methane Emissions: Agriculture, landfills, and natural sources contribute significantly  
    - Effects on Climate: Rising temperatures, extreme weather, and sea level rise  
    - Impact on Ecosystems: Habitat loss, species migration, and biodiversity decline  
    - Societal Effects: Health risks, food security challenges, and economic costs  
    - Mitigation Strategies: Renewable energy, energy efficiency, and carbon capture  
    - Adaptation Measures: Infrastructure resilience and disaster preparedness  
    - International Policies: Paris Agreement and global cooperation efforts  
    - Future Outlook: Importance of urgent action and sustainable development  


---

**Old Descriptor:**
{old_descriptor}

**New Final Summary:**
{final_summary}

---

Your task: Update the descriptor by merging the old descriptor with the new final summary.

Preserve the overall context of the old descriptor but rewrite bullets when needed so the descriptor stays short and relevant.

Merge and rewrite content from the new summary into the existing bullets instead of simply appending it.

Keep it compact: Do not add too many bullets. Combine related points where possible.

Ensure the global summary line reflects the entire scope.

The descriptor must be self-contained and not overly detailed—focus on global topics and key themes.



Output with delimiters:

<<UPDATED_DESCRIPTOR>>
<new descriptor here>
<<UPDATED_DESCRIPTOR>>
""".strip()
