"""
Session Manager Module for SpaceLink
Provides session persistence and resume capabilities.
"""
import uuid
import time
import json
import threading
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta


@dataclass
class SessionState:
    """Represents a session's state."""
    session_id: str
    created_at: float
    last_activity: float
    expires_at: float
    client_info: Dict[str, Any]
    settings: Dict[str, Any]
    connection_count: int


class SessionManager:
    """Manages client sessions for persistence and resume."""
    
    def __init__(self, session_ttl: int = 3600, cleanup_interval: int = 300):
        """
        Initialize session manager.
        
        Args:
            session_ttl: Session time-to-live in seconds (default: 1 hour)
            cleanup_interval: Interval for cleanup thread in seconds
        """
        self._sessions: Dict[str, SessionState] = {}
        self._session_ttl = session_ttl
        self._lock = threading.RLock()
        
        # Start cleanup thread
        self._running = True
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
        
        print(f"[Session] Manager initialized with TTL={session_ttl}s")
    
    def create_session(self, client_info: Optional[Dict] = None) -> Dict:
        """Create a new session."""
        with self._lock:
            session_id = str(uuid.uuid4())
            now = time.time()
            
            session = SessionState(
                session_id=session_id,
                created_at=now,
                last_activity=now,
                expires_at=now + self._session_ttl,
                client_info=client_info or {},
                settings={
                    "fps": 15,
                    "max_width": 1280,
                    "audio_enabled": True,
                    "audio_muted": False,
                    "volume": 1.0,
                    "selected_monitor": 0
                },
                connection_count=1
            )
            
            self._sessions[session_id] = session
            
            print(f"[Session] Created: {session_id[:8]}...")
            
            return {
                "status": "ok",
                "session_id": session_id,
                "expires_in": self._session_ttl,
                "settings": session.settings
            }
    
    def resume_session(self, session_id: str) -> Dict:
        """Resume an existing session."""
        with self._lock:
            if session_id not in self._sessions:
                return {"status": "error", "message": "Session not found", "code": "SESSION_NOT_FOUND"}
            
            session = self._sessions[session_id]
            now = time.time()
            
            # Check if expired
            if now > session.expires_at:
                del self._sessions[session_id]
                return {"status": "error", "message": "Session expired", "code": "SESSION_EXPIRED"}
            
            # Update session
            session.last_activity = now
            session.expires_at = now + self._session_ttl
            session.connection_count += 1
            
            print(f"[Session] Resumed: {session_id[:8]}... (connections: {session.connection_count})")
            
            return {
                "status": "ok",
                "session_id": session_id,
                "expires_in": self._session_ttl,
                "settings": session.settings,
                "connection_count": session.connection_count
            }
    
    def update_session(self, session_id: str, settings: Optional[Dict] = None, 
                       client_info: Optional[Dict] = None) -> Dict:
        """Update session settings or info."""
        with self._lock:
            if session_id not in self._sessions:
                return {"status": "error", "message": "Session not found"}
            
            session = self._sessions[session_id]
            now = time.time()
            
            # Update activity
            session.last_activity = now
            session.expires_at = now + self._session_ttl
            
            # Update settings
            if settings:
                session.settings.update(settings)
            
            if client_info:
                session.client_info.update(client_info)
            
            return {
                "status": "ok",
                "settings": session.settings
            }
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session information."""
        with self._lock:
            if session_id not in self._sessions:
                return None
            
            session = self._sessions[session_id]
            now = time.time()
            
            if now > session.expires_at:
                return None
            
            return {
                "session_id": session.session_id,
                "created_at": session.created_at,
                "last_activity": session.last_activity,
                "expires_in": max(0, session.expires_at - now),
                "settings": session.settings,
                "connection_count": session.connection_count
            }
    
    def end_session(self, session_id: str) -> Dict:
        """End a session explicitly."""
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                print(f"[Session] Ended: {session_id[:8]}...")
                return {"status": "ok", "message": "Session ended"}
            return {"status": "error", "message": "Session not found"}
    
    def touch_session(self, session_id: str) -> bool:
        """Update session activity timestamp."""
        with self._lock:
            if session_id not in self._sessions:
                return False
            
            session = self._sessions[session_id]
            now = time.time()
            
            if now > session.expires_at:
                return False
            
            session.last_activity = now
            session.expires_at = now + self._session_ttl
            return True
    
    def get_active_sessions(self) -> Dict:
        """Get list of active sessions."""
        with self._lock:
            now = time.time()
            active = []
            
            for session_id, session in self._sessions.items():
                if now <= session.expires_at:
                    active.append({
                        "session_id": session_id[:8] + "...",
                        "created_at": datetime.fromtimestamp(session.created_at).isoformat(),
                        "last_activity": datetime.fromtimestamp(session.last_activity).isoformat(),
                        "expires_in": int(session.expires_at - now),
                        "connection_count": session.connection_count
                    })
            
            return {
                "status": "ok",
                "count": len(active),
                "sessions": active
            }
    
    def _cleanup_loop(self):
        """Periodically clean up expired sessions."""
        while self._running:
            time.sleep(60)  # Check every minute
            self._cleanup_expired()
    
    def _cleanup_expired(self):
        """Remove expired sessions."""
        with self._lock:
            now = time.time()
            expired = [sid for sid, session in self._sessions.items() 
                      if now > session.expires_at]
            
            for sid in expired:
                del self._sessions[sid]
                print(f"[Session] Expired: {sid[:8]}...")
            
            if expired:
                print(f"[Session] Cleaned up {len(expired)} expired sessions")
    
    def shutdown(self):
        """Shutdown the session manager."""
        self._running = False
        if self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=2.0)


# Global instance
session_manager = SessionManager()
