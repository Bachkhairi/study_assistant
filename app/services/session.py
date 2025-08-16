from app.memory.session_manager import SessionManager
from app.services.summary_pipeline import SummaryPipeline
from app.services.notion_manager import NotionManager
import os, json, datetime
from pathlib import Path


class SessionService:
    def __init__(self, current: str = None):
        self.sessions = {}
        self.summary_service = SummaryPipeline()
        self.current = current

    def create_session(self, notion_page_id: str, session_title: str):
        manager = SessionManager(notion_page_id=notion_page_id, session_title=session_title)
        self.sessions[manager.session_id] = manager
        return manager.session_id

    def add_summary(self, session_id: str, summary_text: str):
        
        manager = self.sessions[session_id]
        established_summary = manager.notion.get_notion_page()
        first_time = established_summary == ""
        updated_data = self.summary_service.run_with_descriptor(raw_notes=summary_text, session_manager=manager, push_to_notion=True, first_time=first_time, old_descriptor=manager.descriptor, established_summary=established_summary)
        updated_descriptor = updated_data["new_descriptor"]
        return updated_descriptor

    def get_descriptor(self, session_id: str):
        """
        Returns the latest descriptor content (not chat history).
        Ensures it's reloaded from disk if available.
        """
        manager = self.sessions[session_id]

        # Reload descriptor from disk if current.txt exists
        if hasattr(manager, "descriptor") and hasattr(manager.descriptor, "base_dir"):
            manager.descriptor = manager.descriptor.__class__.load(manager.descriptor.base_dir)

        return manager.descriptor.content if hasattr(manager, "descriptor") else ""


    
    def get_history(self, session_id: str):
        return {"history": self.sessions[session_id].chat_history.get_full()}



    def load_all_sessions(self):
    # Pseudocode: load sessions from disk/db
    # For example, read all JSON files in a directory
        sessions_dir = Path(__file__).resolve().parents[2] / "logs"
        for session_id in os.listdir(sessions_dir):
            manager = SessionManager(session_id=session_id)
            self.sessions[manager.session_id] = manager


    def list_sessions(self):
        """
        Returns a dict of all session ids and titles from available sessions.
        Each title comes from metadata.json if available, otherwise falls back to session ID.
        """
        sessions = {}
        sessions_dir = Path(__file__).resolve().parents[2] / "logs"

        self.load_all_sessions()
        
        for session_id in self.sessions:
            session_path = os.path.join(sessions_dir, session_id)
            
            # Skip if session directory doesn't exist
            if not os.path.exists(session_path):
                continue
                
            metadata_path = os.path.join(session_path, "metadata.json")
            title = session_id  # Default to session ID if no title found
            
            try:
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        title = metadata.get('title', session_id)
            except Exception as e:
                print(f"Error loading metadata for session {session_id}: {e}")
                continue
                
            sessions[session_id] = title
        
        return sessions

 