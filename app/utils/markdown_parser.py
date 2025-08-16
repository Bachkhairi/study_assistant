import re
import json

def parse_inline_formatting(text: str):
    parts = []

    # Handle **bold**
    bold_pattern = re.compile(r"\*\*(.+?)\*\*")
    last = 0
    for match in bold_pattern.finditer(text):
        start, end = match.span()
        if start > last:
            parts.append({"type": "text", "text": {"content": text[last:start]}})
        parts.append({
            "type": "text",
            "text": {"content": match.group(1)},
            "annotations": {"bold": True}
        })
        last = end

    if last < len(text):
        parts.append({"type": "text", "text": {"content": text[last:]}})

    return parts if parts else [{"type": "text", "text": {"content": text}}]

def get_indent_level(line: str) -> int:
    # Count number of leading spaces or tabs
    return (len(line) - len(line.lstrip(' '))) // 2  # Adjust spacing as needed

def markdown_to_notion_blocks(markdown_text: str):
    lines = markdown_text.strip().split('\n')
    blocks = []
    current_bullets = []

    def flush_bullets():
        nonlocal current_bullets
        for bullet in current_bullets:
            text = bullet.strip('- ').strip()
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": parse_inline_formatting(text)
                }
            })
        current_bullets.clear()

    for line in lines:
        line = line.strip()
        heading_match = re.match(r'^(#+)\s+(.*)', line)

        if heading_match:
            flush_bullets()
            level = len(heading_match.group(1))
            text = heading_match.group(2)
            block_type = f'heading_{min(level, 3)}'
            blocks.append({
                "object": "block",
                "type": block_type,
                block_type: {
                    "rich_text": parse_inline_formatting(text)
                }
            })
        elif line.startswith('-') or line.startswith('*'):
            current_bullets.append(line)
        elif line:
            flush_bullets()
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": parse_inline_formatting(line)
                }
            })

    flush_bullets()
    return blocks


def parse_between_delimiters(output: str, delimiter: str = "<<FINAL_SUMMARY>>"):
    """
    Extracts content between two occurrences of the same delimiter.
    
    Args:
        output (str): The text containing the content.
        delimiter (str): The delimiter string (e.g., "<<FINAL_SUMMARY>>").
    
    Returns:
        str | None: The extracted content or None if not found.
    """
    pattern = rf"{re.escape(delimiter)}(.*?){re.escape(delimiter)}"
    match = re.search(pattern, output, re.DOTALL)
    return match.group(1).strip() if match else None





def parse_updated_descriptor(llm_output: str) -> str:
    """
    Parses the LLM output and extracts the updated descriptor
    enclosed within <<UPDATED_DESCRIPTOR>> delimiters.
    """
    start_delim = "<<UPDATED_DESCRIPTOR>>"
    end_delim = "<<UPDATED_DESCRIPTOR>>"

    start_idx = llm_output.find(start_delim)
    end_idx = llm_output.rfind(end_delim)

    if start_idx == -1 or end_idx == -1 or start_idx == end_idx:
        raise ValueError("Could not find the updated descriptor delimiters in the LLM output.")

    # Extract the content between the delimiters and strip whitespace
    descriptor = llm_output[start_idx + len(start_delim):end_idx].strip()

    return descriptor

