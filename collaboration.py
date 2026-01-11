"""
Collaboration Module for SpaceLink v4.1
Multi-user session management and real-time sync.
"""
import time
import secrets
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class User:
    """Connected user."""
    user_id: str
    display_name: str
    role: str  # host, viewer, controller
    color: str  # Cursor color
    connected_at: float
    last_activity: float
    cursor_x: float = 0
    cursor_y: float = 0
    is_active: bool = True


class CollaborationSession:
    """Multi-user collaboration session."""
    
    ROLES = {
        "host": {"can_control": True, "can_view": True, "can_kick": True},
        "controller": {"can_control": True, "can_view": True, "can_kick": False},
        "viewer": {"can_control": False, "can_view": True, "can_kick": False}
    }
    
    COLORS = ["#4ade80", "#60a5fa", "#f472b6", "#fbbf24", "#a78bfa", "#fb923c"]
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or secrets.token_hex(8)
        self.users: Dict[str, User] = {}
        self.host_id: Optional[str] = None
        self.created_at = time.time()
        self.max_users = 10
        self.chat_history: List[Dict] = []
        self.color_index = 0
    
    def _get_next_color(self) -> str:
        color = self.COLORS[self.color_index % len(self.COLORS)]
        self.color_index += 1
        return color
    
    def join(self, display_name: str, role: str = "viewer") -> Dict:
        """Add a user to the session."""
        if len(self.users) >= self.max_users:
            return {"status": "error", "message": "Session full"}
        
        user_id = secrets.token_hex(6)
        
        # First user becomes host
        if not self.users:
            role = "host"
            self.host_id = user_id
        
        user = User(
            user_id=user_id,
            display_name=display_name,
            role=role,
            color=self._get_next_color(),
            connected_at=time.time(),
            last_activity=time.time()
        )
        
        self.users[user_id] = user
        
        return {
            "status": "ok",
            "user_id": user_id,
            "session_id": self.session_id,
            "role": role,
            "color": user.color
        }
    
    def leave(self, user_id: str) -> Dict:
        """Remove a user from the session."""
        if user_id in self.users:
            user = self.users.pop(user_id)
            
            # Transfer host if host leaves
            if user_id == self.host_id and self.users:
                new_host = next(iter(self.users.keys()))
                self.users[new_host].role = "host"
                self.host_id = new_host
            
            return {"status": "ok", "message": f"{user.display_name} left"}
        
        return {"status": "error", "message": "User not found"}
    
    def update_cursor(self, user_id: str, x: float, y: float) -> Dict:
        """Update user's cursor position."""
        if user_id in self.users:
            self.users[user_id].cursor_x = x
            self.users[user_id].cursor_y = y
            self.users[user_id].last_activity = time.time()
            return {"status": "ok"}
        return {"status": "error", "message": "User not found"}
    
    def get_cursors(self) -> List[Dict]:
        """Get all users' cursor positions."""
        return [
            {
                "user_id": u.user_id,
                "name": u.display_name,
                "color": u.color,
                "x": u.cursor_x,
                "y": u.cursor_y
            }
            for u in self.users.values()
            if u.is_active
        ]
    
    def send_chat(self, user_id: str, message: str) -> Dict:
        """Send a chat message."""
        if user_id not in self.users:
            return {"status": "error", "message": "User not found"}
        
        chat = {
            "user_id": user_id,
            "name": self.users[user_id].display_name,
            "color": self.users[user_id].color,
            "message": message,
            "timestamp": time.time()
        }
        
        self.chat_history.append(chat)
        if len(self.chat_history) > 100:
            self.chat_history.pop(0)
        
        return {"status": "ok", "chat": chat}
    
    def get_chat(self, limit: int = 50) -> List[Dict]:
        """Get recent chat messages."""
        return self.chat_history[-limit:]
    
    def change_role(self, requester_id: str, target_id: str, new_role: str) -> Dict:
        """Change a user's role (host only)."""
        if requester_id not in self.users or target_id not in self.users:
            return {"status": "error", "message": "User not found"}
        
        if self.users[requester_id].role != "host":
            return {"status": "error", "message": "Only host can change roles"}
        
        if new_role not in self.ROLES:
            return {"status": "error", "message": "Invalid role"}
        
        self.users[target_id].role = new_role
        return {"status": "ok", "message": f"Role changed to {new_role}"}
    
    def kick_user(self, requester_id: str, target_id: str) -> Dict:
        """Kick a user (host only)."""
        if requester_id not in self.users:
            return {"status": "error", "message": "User not found"}
        
        if not self.ROLES[self.users[requester_id].role]["can_kick"]:
            return {"status": "error", "message": "Permission denied"}
        
        return self.leave(target_id)
    
    def get_users(self) -> List[Dict]:
        """Get all connected users."""
        return [asdict(u) for u in self.users.values()]
    
    def get_status(self) -> Dict:
        return {
            "session_id": self.session_id,
            "user_count": len(self.users),
            "created_at": self.created_at,
            "host_id": self.host_id
        }


# Global collaboration session
collab_session = CollaborationSession()


def join_session(display_name: str, role: str = "viewer") -> Dict:
    """Join the collaboration session."""
    return collab_session.join(display_name, role)


def leave_session(user_id: str) -> Dict:
    """Leave the session."""
    return collab_session.leave(user_id)


def get_session_status() -> Dict:
    """Get session status."""
    return collab_session.get_status()


def get_session_users() -> List[Dict]:
    """Get all users in session."""
    return collab_session.get_users()
