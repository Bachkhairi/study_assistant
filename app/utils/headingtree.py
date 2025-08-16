import re
from typing import List, Dict, Any


class HeadingTreeBuilder:
    def __init__(self, headings: List[str]):
        self.headings = headings

    def build_tree(self) -> List[Dict[str, Any]]:
        """
        Builds a tree from markdown-style headings.

        Returns:
            A list of nested dictionaries representing the heading hierarchy.
        """
        tree = []
        stack = []

        for heading in self.headings:
            match = re.match(r"^(#{1,6})\s+(.*)", heading)
            if not match:
                continue

            level = len(match.group(1))
            title = match.group(2).strip()
            node = {"title": title, "children": []}

            # Pop stack until we find parent level
            while stack and stack[-1]["level"] >= level:
                stack.pop()

            if stack:
                stack[-1]["node"]["children"].append(node)
            else:
                tree.append(node)

            stack.append({"level": level, "node": node})

        return tree



