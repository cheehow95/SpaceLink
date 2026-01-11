"""
Macro Recording Module for SpaceLink
Record and playback sequences of commands.
"""
import json
import time
import os
from typing import List, Dict
from datetime import datetime

# Storage directory
MACROS_DIR = os.path.join(os.path.expanduser("~"), "SpaceLink_Macros")
os.makedirs(MACROS_DIR, exist_ok=True)


class MacroRecorder:
    """Records and plays back command sequences."""
    
    def __init__(self):
        self.recording = False
        self.commands: List[Dict] = []
        self.start_time = 0
        self.current_name = ""
    
    def start_recording(self, name: str = None) -> dict:
        """Start recording a macro."""
        if self.recording:
            return {"status": "error", "message": "Already recording"}
        
        self.recording = True
        self.commands = []
        self.start_time = time.time()
        self.current_name = name or f"macro_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return {"status": "ok", "message": f"Recording: {self.current_name}"}
    
    def stop_recording(self) -> dict:
        """Stop recording and save the macro."""
        if not self.recording:
            return {"status": "error", "message": "Not recording"}
        
        self.recording = False
        
        # Save macro to file
        filepath = os.path.join(MACROS_DIR, f"{self.current_name}.json")
        with open(filepath, "w") as f:
            json.dump({
                "name": self.current_name,
                "created": datetime.now().isoformat(),
                "commands": self.commands
            }, f, indent=2)
        
        count = len(self.commands)
        self.commands = []
        
        return {
            "status": "ok",
            "message": f"Saved: {self.current_name} ({count} commands)",
            "filename": f"{self.current_name}.json"
        }
    
    def record_command(self, command: dict):
        """Record a command during macro recording."""
        if not self.recording:
            return
        
        self.commands.append({
            "timestamp": time.time() - self.start_time,
            "command": command
        })
    
    def get_macros(self) -> List[Dict]:
        """List all saved macros."""
        macros = []
        for filename in os.listdir(MACROS_DIR):
            if filename.endswith(".json"):
                filepath = os.path.join(MACROS_DIR, filename)
                try:
                    with open(filepath, "r") as f:
                        data = json.load(f)
                        macros.append({
                            "name": data.get("name", filename[:-5]),
                            "created": data.get("created", "Unknown"),
                            "command_count": len(data.get("commands", []))
                        })
                except:
                    pass
        return macros
    
    def load_macro(self, name: str) -> dict:
        """Load a macro by name."""
        filepath = os.path.join(MACROS_DIR, f"{name}.json")
        if not os.path.exists(filepath):
            return {"status": "error", "message": "Macro not found"}
        
        with open(filepath, "r") as f:
            data = json.load(f)
        
        return {
            "status": "ok",
            "name": data.get("name"),
            "commands": data.get("commands", [])
        }
    
    def delete_macro(self, name: str) -> dict:
        """Delete a macro."""
        filepath = os.path.join(MACROS_DIR, f"{name}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
            return {"status": "ok", "message": f"Deleted: {name}"}
        return {"status": "error", "message": "Macro not found"}
    
    def is_recording(self) -> bool:
        return self.recording


# Global macro recorder instance
macro_recorder = MacroRecorder()
