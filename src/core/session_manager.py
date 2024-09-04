import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class Session:
    """Initializes a session with session ID, user ID, and timestamps."""

    def __init__(self, session_id: str, user_id: str):
        self.session_id = session_id
        self.user_id = user_id
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.data: Dict[str, Any] = {}

    def update_last_accessed(self):
        """Updates the last accessed timestamp of the session."""
        self.last_accessed = datetime.now()


class SessionManager:
    """Manages user sessions, including creation, validation, and deletion."""

    """useful for expanding the functionality of this application in the future. However, it's not currently integrated into the main application flow."""

    def __init__(self, session_timeout: int = 30):
        """Initializes the session manager with a session timeout period."""
        self.sessions: Dict[str, Session] = {}
        self.session_timeout = timedelta(minutes=session_timeout)

    def create_session(self, user_id: str) -> str:
        """Creates a new session for a user and returns the session ID."""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = Session(session_id, user_id)
        return session_id

    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieves a session by session ID and updates its last accessed time."""
        session = self.sessions.get(session_id)
        if session:
            session.update_last_accessed()
        return session

    def is_valid_session(self, session_id: str) -> bool:
        """Checks if a session is valid based on its last accessed time."""
        session = self.get_session(session_id)
        if not session:
            return False
        if datetime.now() - session.last_accessed > self.session_timeout:
            self.delete_session(session_id)
            return False
        return True

    def delete_session(self, session_id: str):
        """Deletes a session by session ID."""
        if session_id in self.sessions:
            del self.sessions[session_id]


session_manager = SessionManager()


def get_or_create_session_id(x_session_id: Optional[str] = None) -> str:
    """Gets an existing session ID or creates a new one if invalid or missing."""
    if x_session_id and session_manager.is_valid_session(x_session_id):
        return x_session_id
    return session_manager.create_session(str(uuid.uuid4()))


# Export the necessary components
__all__ = ["SessionManager", "session_manager", "get_or_create_session_id"]
