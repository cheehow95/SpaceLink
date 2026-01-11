"""
Audit Log Module for SpaceLink v4.1
Session logging and security audit trail.
"""
import os
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
from collections import deque

# Log directory
AUDIT_DIR = os.path.join(os.path.expanduser("~"), "SpaceLink_Logs")
os.makedirs(AUDIT_DIR, exist_ok=True)


class AuditLog:
    """Audit logging for security and session tracking."""
    
    EVENT_TYPES = {
        "connection": "🔌",
        "disconnect": "❌",
        "auth_success": "✅",
        "auth_failure": "🚫",
        "command": "⌨️",
        "file_access": "📁",
        "power": "⚡",
        "settings": "⚙️",
        "error": "❗"
    }
    
    def __init__(self, max_memory_entries: int = 1000):
        self.entries = deque(maxlen=max_memory_entries)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(AUDIT_DIR, f"audit_{self.session_id}.json")
    
    def log(self, event_type: str, message: str, details: Optional[Dict] = None, 
            user_id: str = "system", ip_address: str = "localhost"):
        """Log an event."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "message": message,
            "user_id": user_id,
            "ip_address": ip_address,
            "details": details or {}
        }
        
        self.entries.append(entry)
        self._write_to_file(entry)
        
        icon = self.EVENT_TYPES.get(event_type, "📝")
        print(f"[Audit] {icon} {event_type}: {message}")
    
    def _write_to_file(self, entry: Dict):
        """Append entry to log file."""
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"[Audit] Write failed: {e}")
    
    def get_entries(self, limit: int = 50, event_type: Optional[str] = None) -> List[Dict]:
        """Get recent log entries."""
        entries = list(self.entries)
        
        if event_type:
            entries = [e for e in entries if e["event_type"] == event_type]
        
        return entries[-limit:]
    
    def get_sessions(self) -> List[Dict]:
        """Get list of all audit log files."""
        sessions = []
        for filename in os.listdir(AUDIT_DIR):
            if filename.startswith("audit_") and filename.endswith(".json"):
                filepath = os.path.join(AUDIT_DIR, filename)
                sessions.append({
                    "filename": filename,
                    "session_id": filename[6:-5],
                    "size_kb": round(os.path.getsize(filepath) / 1024, 2),
                    "created": datetime.fromtimestamp(os.path.getctime(filepath)).isoformat()
                })
        return sorted(sessions, key=lambda x: x["created"], reverse=True)
    
    def export_session(self, session_id: str) -> Optional[str]:
        """Export a session log as JSON string."""
        filepath = os.path.join(AUDIT_DIR, f"audit_{session_id}.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        return None
    
    def get_statistics(self) -> Dict:
        """Get audit statistics."""
        entries = list(self.entries)
        stats = {"total": len(entries), "by_type": {}}
        
        for entry in entries:
            t = entry["event_type"]
            stats["by_type"][t] = stats["by_type"].get(t, 0) + 1
        
        return stats


# Global audit log
audit_log = AuditLog()


def log_event(event_type: str, message: str, details: Dict = None):
    """Log an audit event."""
    audit_log.log(event_type, message, details)


def get_audit_entries(limit: int = 50) -> List[Dict]:
    """Get recent audit entries."""
    return audit_log.get_entries(limit)


def get_audit_stats() -> Dict:
    """Get audit statistics."""
    return audit_log.get_statistics()
