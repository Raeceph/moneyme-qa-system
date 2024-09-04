from typing import List, Dict
from collections import deque
import time


class ConversationManager:
    """Manage conversations for different sessions, handling message history and pruning old conversations."""

    def __init__(self, max_history: int = 10):
        """Initialize the conversation manager with a maximum history length for each session."""
        self.max_history = max_history
        self.conversations: Dict[str, deque] = {}

    def add_message(self, session_id: str, role: str, content: str):
        """Add a message to the conversation history for a specific session."""
        if session_id not in self.conversations:
            self.conversations[session_id] = deque(maxlen=self.max_history)

        self.conversations[session_id].append(
            {"role": role, "content": content, "timestamp": time.time()}
        )

    def get_conversation(self, session_id: str) -> List[Dict]:
        """Retrieve the full conversation history for a specific session."""
        return list(self.conversations.get(session_id, []))

    def clear_conversation(self, session_id: str):
        """Clear the conversation history for a specific session."""
        if session_id in self.conversations:
            del self.conversations[session_id]

    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """Get the conversation history for a session, returning only role and content."""
        conversation = self.get_conversation(session_id)
        return [
            {"role": msg["role"], "content": msg["content"]} for msg in conversation
        ]

    def get_conversation_summary(self, session_id: str) -> str:
        """Generate a summary of the conversation for a specific session."""
        conversation = self.get_conversation(session_id)
        summary = []
        for message in conversation:
            role = "Human" if message["role"] == "user" else "AI"
            summary.append(f"{role}: {message['content']}")
        return "\n".join(summary)

    def prune_old_conversations(self, max_age: float = 3600):
        """Remove conversations that have messages older than the specified max age.- good to haev functions"""
        current_time = time.time()
        for session_id in list(self.conversations.keys()):
            if self.conversations[session_id]:
                oldest_message = self.conversations[session_id][0]
                if current_time - oldest_message["timestamp"] > max_age:
                    del self.conversations[session_id]
