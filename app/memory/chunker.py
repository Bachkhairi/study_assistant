import re
from typing import List
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document


class SummaryChunker:
    def __init__(self, max_chunks: int = 20):
        self.max_chunks = max_chunks  # optional limit to prevent memory overload

    def chunk_by_heading(self, summary: str) -> List[str]:
        """
        Extracts just the heading text from markdown headings (#, ##, ###).
        Returns clean heading text without # symbols, newlines, or content.
        """
        lines = summary.strip().split('\n')
        headings = []

        for line in lines:
            stripped = line.strip()
            
            # Check if this line is a heading
            if re.match(r"^#{1,6}\s", stripped):
                # Keep the heading text with # symbols, just clean up extra spaces
                heading_text = stripped.strip()
                if heading_text:  # Only add non-empty headings
                    headings.append(heading_text)

        return headings[:self.max_chunks]



    def chunk_by_paragraphs(self, summary: str) -> List[str]:
        """
        Splits the markdown summary into chunks, each chunk containing the paragraphs 
        under a heading (excluding the heading line itself), ignoring chunks that
        contain only horizontal rules or are empty.

        Returns:
            List[str]: List of paragraph chunks grouped under each heading.
        """
        lines = summary.strip().split('\n')
        chunks = []
        current_chunk = []
        inside_code_block = False
        started = False  # To track if we found the first heading yet

        for line in lines:
            stripped = line.strip()

            # Toggle code block state
            if stripped.startswith("```"):
                inside_code_block = not inside_code_block
                current_chunk.append(stripped)
                continue

            # Check if this line is a heading and we're not inside a code block
            if not inside_code_block and re.match(r"^#{1,6}\s", stripped):
                # Save previous chunk if meaningful
                if started and current_chunk:
                    joined = "\n".join(current_chunk).strip()
                    # Skip if chunk is empty or just horizontal rules
                    if joined and joined != "---":
                        chunks.append(joined)
                    current_chunk = []
                started = True
                # skip heading line itself
                continue

            if started:
                # Ignore standalone horizontal rules in content lines
                if not inside_code_block and stripped == "---":
                    continue
                current_chunk.append(stripped)

        # Flush last chunk
        if current_chunk:
            joined = "\n".join(current_chunk).strip()
            if joined and joined != "---":
                chunks.append(joined)

        return chunks[:self.max_chunks]


    #unused
    def attach_hierarchy(self, chunks: List[str], page_name: str) -> List[dict]:
        """
        Attach hierarchical breadcrumbs to heading chunks.
        Example: Page > H1 > H2 > H3
        """
        results = []
        stack = [page_name]  # Start with the page name

        for chunk in chunks:
            heading_match = re.match(r"^(#+)\s+(.*)", chunk)
            if heading_match:
                level = len(heading_match.group(1))  # number of # indicates level
                title = heading_match.group(2).strip()

                # Adjust stack: trim or expand based on heading level
                if len(stack) > level:
                    stack = stack[:level]
                elif len(stack) < level:
                    # Fill missing levels (rare, but keep it safe)
                    while len(stack) < level:
                        stack.append("")

                # Update current level title
                if len(stack) == level:
                    stack[-1] = title
                else:
                    stack.append(title)

                context = " > ".join([s for s in stack if s])  # Ignore empty placeholders
                results.append({
                    "chunk": chunk,
                    "context": context
                })

        return results
    



    def chunk_with_hierarchy(self, page_name: str, content: str, max_chunks: int = 100) -> List[dict[str, str]]:
        """
        Parses the markdown text content, tracks heading hierarchy (#, ##, ###),
        chunks paragraphs under headings, and returns chunks with full context.

        Args:
            page_name (str): The root page name (top-level context).
            content (str): The full markdown content to chunk.
            max_chunks (int): Maximum number of chunks to return.

        Returns:
            List[Dict]: Each dict has keys:
                - "context": full hierarchy breadcrumb (e.g. "Page > Heading1 > Subheading")
                - "chunk": the text chunk under that context
        """
        lines = content.strip().split('\n')
        stack = [page_name]  # Stack holds the current hierarchy
        chunks = []

        current_level = 0
        current_paragraph_lines = []

        position_counter = 0

        def flush_paragraph():
            nonlocal position_counter
            if current_paragraph_lines:
                paragraph_text = "\n".join(current_paragraph_lines).strip()
                if paragraph_text:
                    chunks.append({
                        "context": " > ".join(stack),
                        "chunk": paragraph_text,
                        "position": position_counter
                    })
                    position_counter += 1
                current_paragraph_lines.clear()

        for line in lines:
            heading_match = re.match(r'^(#{1,6})\s+(.*)', line.strip())
            if heading_match:
                # New heading found: flush current paragraph
                flush_paragraph()

                level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip()

                # Adjust stack to current heading level
                # Example: if level=2, stack should have 2 elements after page_name, so total 3
                while len(stack) > level:
                    stack.pop()
                while len(stack) < level:
                    stack.append("")

                stack[-1] = heading_text
                current_level = level

            else:
                # Regular content line, add to current paragraph buffer
                if line.strip() == "" and current_paragraph_lines:
                    # Blank line signals paragraph break, flush
                    flush_paragraph()
                else:
                    current_paragraph_lines.append(line)

            # Stop if max chunks reached
            if len(chunks) >= max_chunks:
                break

        # Flush last paragraph
        flush_paragraph()

        return chunks[:max_chunks]
    

    def semantic_subchunk_paragraph(self, data_items, min_len_for_chunking=500):
        """
        Further chunk paragraphs using semantic similarity if they exceed a length threshold.

        Parameters:
            data_items (list[dict]): List of dicts with keys: page, h1, h2, h3, paragraph, block_ids, combined_heading
            min_len_for_chunking (int): Minimum character length to apply semantic chunking

        Returns:
            list[dict]: List with semantically sub-chunked paragraphs, preserving metadata and appending combined_heading
        """
        result = []
        model_name = "sentence-transformers/all-mpnet-base-v2"
        embeddings = HuggingFaceEmbeddings(model_name=model_name)
        splitter = SemanticChunker(embeddings, add_start_index=True)

        for item in data_items:
            paragraph = item["paragraph"]
            combined_heading = item.get("combined_heading", "")
            metadata = {k: item.get(k) for k in ["page_id","page", "h1", "h2", "h3", "block_ids"]}

            if len(paragraph.strip()) < min_len_for_chunking:
                # Skip semantic chunking and return original paragraph with combined_heading appended
                result.append({
                    **metadata,
                    "paragraph": f"{combined_heading}:{paragraph.strip()}"
                })
                continue

            # Create a Document with metadata
            doc = Document(page_content=paragraph, metadata=metadata)

            # Perform semantic chunking
            subchunks = splitter.split_documents([doc])

            for subdoc in subchunks:
                result.append({
                    **metadata,
                    "paragraph": f"{combined_heading}:{subdoc.page_content.strip()}"
                })

        return result
