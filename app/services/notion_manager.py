import os
from notion_client import Client
from dotenv import load_dotenv
from app.utils.markdown_parser import markdown_to_notion_blocks
import json
from pathlib import Path

load_dotenv()

class NotionManager:
    def __init__(self, folder_id:str = os.getenv("NOTION_FOLDER_ID"),page_id: str = os.getenv("NOTION_PAGE_ID")):
        self.notion = Client(auth=os.getenv("NOTION_API_KEY"))
        self.page_id = page_id 
        self.folder_id = folder_id
        self.output_dir = Path(__file__).resolve().parents[2]

    def write_to_notion(self, markdown: str):
        """
        Converts markdown into Notion blocks and appends them to the page.
        """
        blocks = markdown_to_notion_blocks(markdown)
        response = self.notion.blocks.children.append(
            block_id=self.page_id,
            children=blocks
        )
        


    def has_content_blocks(self, page_id: str) -> bool:
        cursor = None
        while True:
            response = self.notion.blocks.children.list(block_id=page_id, start_cursor=cursor)
            for block in response.get("results", []):
                if block["type"] != "child_page":  # Means actual content block
                    return True
            if not response.get("has_more"):
                break
            cursor = response.get("next_cursor")
        return False
    

    def get_notion_page(self) -> str:
        """
        Fetches content from the Notion page and reconstructs it as markdown,
        recursively fetching nested blocks (children). Returns "(No content found)" if no content.
        """
        def fetch_blocks(block_id, indent_level=0):
            texts = []
            cursor = None
            indent = "  " * indent_level  # Two spaces per indent level
            has_content = False  # Track if we find any actual content

            while True:
                response = self.notion.blocks.children.list(
                    block_id=block_id,
                    start_cursor=cursor
                )
                blocks = response["results"]

                for block in blocks:
                    block_type = block["type"]
                    block_id = block["id"]
                    
                    # 👍 Skip sub-pages since they aren't page content
                    if block_type == "child_page":
                        continue
                    
                    # Extract text content if exists
                    rich_text = block[block_type].get("rich_text", [])
                    text = "".join([t["text"]["content"] for t in rich_text if t["type"] == "text"]).strip()

                    # Check if current block has meaningful content
                    if text or block_type in ["code", "image", "divider", "toggle"]:
                        has_content = True
                        
                        if block_type == "heading_1":
                            texts.append(f"{indent}# {text}")
                        elif block_type == "heading_2":
                            texts.append(f"{indent}## {text}")
                        elif block_type == "heading_3":
                            texts.append(f"{indent}### {text}")
                        elif block_type == "bulleted_list_item":
                            texts.append(f"{indent}- {text}")
                        elif block_type == "numbered_list_item":
                            texts.append(f"{indent}1. {text}")
                        elif block_type == "quote":
                            texts.append(f"{indent}> {text}")
                        elif block_type == "code":
                            lang = block[block_type].get("language", "")
                            texts.append(f"{indent}```{lang}\n{text}\n{indent}```")
                        elif block_type == "paragraph":
                            texts.append(f"{indent}{text}")
                        elif block_type == "divider":
                            texts.append(f"{indent}---")
                        elif block_type == "toggle":
                            # Toggle heading with content below it
                            texts.append(f"{indent}<details>\n{indent}<summary>{text}</summary>\n")
                        elif block_type == "image":
                            # Attempt to extract image URL (may require adjustments)
                            image_url = block[block_type].get("file", {}).get("url", "")
                            if image_url:
                                texts.append(f"{indent}![Image]({image_url})")
                            else:
                                texts.append(f"{indent}![Image]")
                        else:
                            # For any other blocks, just add the text if available
                            if text:
                                texts.append(f"{indent}{text}")

                    # Recursively fetch children if present
                    if block.get("has_children"):
                        child_texts = fetch_blocks(block["id"], indent_level + 1)
                        if child_texts:
                            # Add a blank line before and after nested content for readability
                            texts.append(f"\n{child_texts}\n")
                            has_content = True

                if not response.get("has_more"):
                    break

                cursor = response.get("next_cursor")

            return "\n".join(texts) if has_content else ""

        content = fetch_blocks(self.page_id)
        return content if content else "(No content found)"

    def get_all_pages_in_hierarchy(self, parent_id: str, pages_meta: dict = None) -> dict:
        """
        Recursively retrieve all child pages under a parent page (folder) in Notion
        by using blocks.children.list to get direct children blocks.

        :param parent_id: The Notion page ID of the parent folder.
        :param pages_meta: A dictionary to store metadata for all retrieved pages.
        :return: Dictionary with page_id as keys and metadata as values.
        """
        if pages_meta is None:
            pages_meta = {}

        cursor = None
        while True:
            response = self.notion.blocks.children.list(
                block_id=parent_id,
                start_cursor=cursor,
                page_size=100
            )

            for block in response.get("results", []):
                # We only care about child blocks that are pages
                if block.get("type") == "child_page":
                    page_id = block["id"]
                    title = block["child_page"].get("title", "(untitled)")

                    pages_meta[page_id] = {
                        "id": page_id,
                        "title": title,
                        "parent_id": parent_id,
                        # pages retrieved via blocks.children.list don't always have properties,
                        # so url and timestamps may need separate retrieval if needed
                    }

                    # Recurse into this child page to get its children pages
                    self.get_all_pages_in_hierarchy(page_id, pages_meta)

                # If you want to support child databases or other block types, handle here

            if not response.get("has_more"):
                break
            cursor = response.get("next_cursor")

        return pages_meta


    def fetch(self, pages_meta: dict) -> list[dict]:
        """
        Fetch markdown content for each page_id and merge it with metadata.
        :param pages_meta: Dictionary with page_id as key and metadata (title, parent_id) as value.
        :return: List of dictionaries containing merged metadata and markdown content.
        """
        dataset = []
        original_page_id = self.page_id

        for page_id, meta in pages_meta.items():
            # Temporarily set the instance's page_id
            self.page_id = page_id
            content = self.get_notion_page()
            if content == "(No content found)":
                continue
            # Only add if content exists
            if content.strip():
                dataset.append({
                    "page_id": page_id,
                    "title": meta["title"],
                    "parent_id": meta["parent_id"],
                    "content": content
                })

        self.page_id = original_page_id
        print(f"Total pages with content: {len(dataset)}\n")
        return dataset


    def export_to_filesystem(self, folder_name: str = ""):
        """
        Export pages dataset into a folder structure:
        data/
        pages_meta.json
        pages_content/<page_id>.md
        """
        # Pull data from Notion
        pages_meta = self.get_all_pages_in_hierarchy(self.folder_id)
        dataset = self.fetch(pages_meta)

        # Determine base folder (default to "data")
        base_dir = getattr(self, "output_dir", "data")
        output_dir = os.path.join(base_dir, folder_name)
        os.makedirs(output_dir, exist_ok=True)

        # Create pages_content folder
        content_dir = os.path.join(output_dir, "pages_content")
        os.makedirs(content_dir, exist_ok=True)

        # Build metadata dict & write content files
        updated_meta = {}
        for item in dataset:
            page_id = item["page_id"]
            title = "_".join(item["title"].split())
            # Update metadata
            updated_meta[page_id] = {
                "title": title,
                "parent_id": item["parent_id"]
            }

            # Write content to markdown
            content_path = os.path.join(content_dir, f"{title}.md")
            with open(content_path, "w", encoding="utf-8") as f:
                f.write(item["content"])

        # Save updated metadata JSON
        meta_path = os.path.join(output_dir, "pages_meta.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(updated_meta, f, ensure_ascii=False, indent=2)

        print(f"✅ Export completed: {len(dataset)} pages saved to {output_dir}/")



    def get_pages_hierarchy(self, parent_id: str, pages_meta: dict = None, folder_name: str = "AI-assistant") -> dict:
        """
        Recursively retrieve all child pages under a parent page (folder) in Notion
        using blocks.children.list to get direct children blocks.

        :param parent_id: The Notion page ID of the parent folder.
        :param pages_meta: A dictionary to store metadata for all retrieved pages.
        :return: Dictionary with page_id as keys and metadata as values.
        """
        if pages_meta is None:
            pages_meta = {}

        base_dir = getattr(self, "output_dir", "data")
        output_dir = os.path.join(base_dir, folder_name)
        os.makedirs(output_dir, exist_ok=True)

        cursor = None
        while True:
            response = self.notion.blocks.children.list(
                block_id=parent_id,
                start_cursor=cursor,
                page_size=100
            )

            for block in response.get("results", []):
                if block.get("type") == "child_page":
                    page_id = block["id"]
                    title = block["child_page"].get("title", "(untitled)")

                    # Collect all blocks inside this page
                    page_blocks = []
                    block_cursor = None
                    while True:
                        block_resp = self.notion.blocks.children.list(
                            block_id=page_id,
                            start_cursor=block_cursor,
                            page_size=100
                        )
                        page_blocks.extend(block_resp.get("results", []))
                        if not block_resp.get("has_more"):
                            break
                        block_cursor = block_resp.get("next_cursor")

                    # Clean and normalize block content for JSON
                    normalized_blocks = []
                    for blk in page_blocks:
                        blk_type = blk.get("type")
                        content = blk.get(blk_type, {}) if blk_type else {}

                        # Optional: strip out rich_text for easier saving
                        if isinstance(content, dict) and "rich_text" in content:
                            content["rich_text"] = [
                                rt.get("plain_text", "") for rt in content["rich_text"]
                            ]

                        normalized_blocks.append({
                            "id": blk.get("id"),
                            "type": blk_type,
                            "content": content
                        })

                    pages_meta[page_id] = {
                        "id": page_id,
                        "title": title,
                        "parent_id": parent_id,
                        "blocks": normalized_blocks
                    }

                    # Recurse into this child page
                    self.get_pages_hierarchy(page_id, pages_meta)

            if not response.get("has_more"):
                break
            cursor = response.get("next_cursor")

        # Save to disk safely
        meta_file = os.path.join(output_dir, "metadata.json")
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(pages_meta, f, indent=2, ensure_ascii=False)

        return pages_meta


    def get_all_pages_in_hierarchy_grouped(self, data_by_page_id: dict, folder_name: str = "AI-assistant"):
        all_paragraphs = []

        def get_parent_path(page_id):
            path = []
            visited = set()
            while page_id and page_id not in visited:
                visited.add(page_id)
                page = data_by_page_id.get(page_id)
                if not page:
                    break
                title = page.get("title", "").strip()
                if title:
                    path.append(title)
                page_id = page.get("parent_id")
            return list(reversed(path))

        for page_id, page in data_by_page_id.items():
            page_name = page.get("title", "")
            blocks = page.get("blocks", [])

            current_h1 = None
            current_h2 = None
            current_h3 = None
            grouped = []
            block_ids = []

            parent_path = get_parent_path(page.get("parent_id"))  # ⚠️ You want parent of current page
            # ✅ Remove root if it matches folder_name
            if parent_path and parent_path[0] == folder_name:
                parent_path = parent_path[1:]

            parent_path_str = " > ".join(parent_path)

            def extract_text(rich_text):
                if isinstance(rich_text, list):
                    return "".join(
                        t if isinstance(t, str) else t.get("text", "")
                        for t in rich_text
                    ).strip()
                return ""

            def flush_group():
                nonlocal grouped, block_ids
                if grouped:
                    item = {
                        "page_id": page_id,
                        "page": page_name,
                        "page_hierarchy_path": parent_path_str,
                        "h1": current_h1,
                        "h2": current_h2,
                        "h3": current_h3,
                        "paragraph": " ".join(grouped),
                        "block_ids": block_ids[:]
                    }

                    # ✅ Final combined_heading = path + headings
                    heading_parts = parent_path + [page_name, current_h1, current_h2, current_h3]
                    valid = [h.strip() for h in heading_parts if h and isinstance(h, str) and h.strip()]
                    item["combined_heading"] = " > ".join(valid)

                    all_paragraphs.append(item)
                    grouped = []
                    block_ids = []

            for block in blocks:
                block_type = block.get("type")
                content = block.get("content", {})
                text = extract_text(content.get("rich_text", []))
                block_id = block.get("id")

                if block_type == "heading_1":
                    flush_group()
                    current_h1 = text
                    current_h2 = None
                    current_h3 = None
                elif block_type == "heading_2":
                    flush_group()
                    current_h2 = text
                    current_h3 = None
                elif block_type == "heading_3":
                    flush_group()
                    current_h3 = text
                elif block_type in {
                    "paragraph", "quote", "bulleted_list_item", "numbered_list_item",
                    "callout", "code", "image", "bookmark", "toggle"
                }:
                    if text:
                        grouped.append(text)
                        block_ids.append(block_id)

            flush_group()

        # ✅ Save result
        base_dir = getattr(self, "output_dir", "data")
        output_dir = os.path.join(base_dir, folder_name)
        os.makedirs(output_dir, exist_ok=True)
        meta_file = os.path.join(output_dir, "chunks.json")
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(all_paragraphs, f, indent=2, ensure_ascii=False)

        return all_paragraphs


    
    def add_combined_heading(self, folder_name: str):
        base_dir = getattr(self, "output_dir", "data")
        output_dir = os.path.join(base_dir, folder_name)
        meta_file = os.path.join(output_dir, "pre_chunks.json")
        with open(meta_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for item in data:
            combined = item["page"]
            headings = [item["h1"], item["h2"], item["h3"]]
            for heading in headings:
                if heading is not None:
                    combined += ">" + heading
            item["combined_heading"] = combined
        output_path = os.path.join(output_dir, "chunks.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return data
    


    