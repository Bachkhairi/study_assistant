import os
import uuid
import datetime
from app.memory.chat_history import ChatHistory
from app.utils.descriptor import Descriptor
from app.services.notion_manager import NotionManager
from pathlib import Path
import json
SESSIONS_DIR = Path(__file__).resolve().parents[2] / "logs"


class SessionManager:
    def __init__(self, base_dir=SESSIONS_DIR, session_title=None, notion_page_id=None, session_id=None):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

        # Session ID setup
        self.session_id = session_id or self._generate_session_id()
        self.session_dir = os.path.join(base_dir, self.session_id)
        os.makedirs(self.session_dir, exist_ok=True)

        # Metadata file
        self.metadata_path = os.path.join(self.session_dir, "metadata.json")
        if os.path.exists(self.metadata_path):
            # Load existing metadata
            with open(self.metadata_path, "r") as f:
                metadata = json.load(f)
            self.notion_page_id = metadata.get("notion_page_id")
            self.session_title = metadata.get("title")
        else:
            # Save new metadata
            self.notion_page_id = notion_page_id
            self.session_title = session_title
            self._create_metadata_file(session_title)

        # Notion manager
        self.notion = NotionManager(page_id=self.notion_page_id, folder_id=None)

        # Descriptor
        descriptor_dir = os.path.join(self.session_dir, "descriptor")
        self.descriptor = Descriptor.load(descriptor_dir)

        # Chat history
        self.chat_history_path = os.path.join(self.session_dir, "chat_history.json")
        self.chat_history = ChatHistory()
        if os.path.exists(self.chat_history_path):
            self.chat_history.load(self.chat_history_path)

        # Log file
        self.log_path = os.path.join(self.session_dir, "session.log")

    def _generate_session_id(self):
        return str(uuid.uuid4())[:8]
    

    def _create_metadata_file(self, session_title=None):
        """Create metadata.json with session information"""
        metadata = {
            "title": session_title,
            "creation_date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "session_id": self.session_id,
            "notion_page_id": self.notion_page_id
        }

        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

    def save(self):
        self.chat_history.save(self.chat_history_path)

    def log(self, message: str):
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(f"[{self.timestamp}] {message}\n")

    def add_turn(self, user_msg: str, assistant_msg: str):
        self.chat_history.add_turn(user_msg, assistant_msg)
        self.save()


