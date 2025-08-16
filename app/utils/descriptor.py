import os
from datetime import datetime
from app.utils.markdown_parser import parse_updated_descriptor


class Descriptor:
    def __init__(self, base_dir: str , content: str = ""):
        self.content = content
        self.base_dir = base_dir

    def update(self, final_summary: str = ""):
        """
        Updates the descriptor content and automatically saves it to 'current.txt'
        and appends the new version to a history folder.
        """
        from app.chains.generation_chain import GenerationChain
        generation_chain = GenerationChain()
        output = generation_chain.build_descriptor(
            old_descriptor=self,
            final_summary=final_summary
        )
        new_descriptor = parse_updated_descriptor(output)
        self.content = new_descriptor

        # Save the updated descriptor (both current and history)
        self._save_with_history()

        return self.content

    def _save_with_history(self):
        """
        Saves current descriptor to current.txt and also creates a versioned copy
        in a history folder using timestamp-based filenames.
        """
        os.makedirs(self.base_dir, exist_ok=True)
        history_dir = os.path.join(self.base_dir, "history")
        os.makedirs(history_dir, exist_ok=True)

        # Save as current.txt
        current_path = os.path.join(self.base_dir, "current.txt")
        with open(current_path, "w") as f:
            f.write(self.content)

        # Save in history with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        history_path = os.path.join(history_dir, f"descriptor_{timestamp}.txt")
        with open(history_path, "w") as f:
            f.write(self.content)

    def save(self, path: str):
        """Manual save (if needed outside update logic)."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(self.content)

    
    @classmethod
    def load(cls, base_dir: str):
        """
        Loads descriptor from base_dir if current.txt exists; else returns empty.
        """
        current_path = os.path.join(base_dir, "current.txt")
        if os.path.exists(current_path):
            with open(current_path, "r", encoding="utf-8") as f:
                return cls(base_dir, f.read())
        return cls(base_dir, "")