import json
from typing import List, Dict, Optional


class ChatHistory:
    def __init__(self, history: Optional[List[Dict[str, str]]] = None):
        self.history = history if history is not None else []

    def add_turn(self, user_msg: str, assistant_msg: str, role_1: str = "user",role_2: str = "assistant"):
        self.history.append({"role": role_1, "content": user_msg})
        self.history.append({"role": role_2, "content": assistant_msg})

    def get_recent(self, n: int = 5) -> List[Dict[str, str]]:
        """Returns the last n turns (each turn is two messages)."""
        return self.history[-n * 2:]

    def get_full(self) -> List[Dict[str, str]]:
        return self.history

    def save(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)

    def load(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            self.history = json.load(f)

    def to_markdown(self) -> str:
        return "\n\n".join(
            f"**{entry['role'].capitalize()}**:\n{entry['content']}"
            for entry in self.history
        )
