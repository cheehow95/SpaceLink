"""
Whiteboard Module for SpaceLink v4.1
Collaborative drawing and annotation.
"""
import json
import time
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from collections import deque


@dataclass
class DrawAction:
    """A drawing action on the whiteboard."""
    action_type: str  # line, circle, rect, text, erase
    x1: float
    y1: float
    x2: float = 0
    y2: float = 0
    color: str = "#ffffff"
    thickness: int = 2
    text: str = ""
    user_id: str = "default"
    timestamp: float = 0
    
    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = time.time()


class Whiteboard:
    """Collaborative whiteboard for annotations."""
    
    def __init__(self, max_actions: int = 1000):
        self.actions: deque = deque(maxlen=max_actions)
        self.undo_stack: List[DrawAction] = []
        self.users: Dict[str, Dict] = {}
    
    def add_action(self, action: DrawAction) -> Dict:
        """Add a drawing action."""
        self.actions.append(action)
        self.undo_stack.clear()  # Clear redo stack on new action
        
        return {"status": "ok", "action_id": len(self.actions)}
    
    def draw_line(self, x1: float, y1: float, x2: float, y2: float,
                  color: str = "#ffffff", thickness: int = 2, user_id: str = "default"):
        """Draw a line."""
        action = DrawAction("line", x1, y1, x2, y2, color, thickness, user_id=user_id)
        return self.add_action(action)
    
    def draw_circle(self, x: float, y: float, radius: float,
                    color: str = "#ffffff", thickness: int = 2, user_id: str = "default"):
        """Draw a circle."""
        action = DrawAction("circle", x, y, radius, 0, color, thickness, user_id=user_id)
        return self.add_action(action)
    
    def draw_rect(self, x1: float, y1: float, x2: float, y2: float,
                  color: str = "#ffffff", thickness: int = 2, user_id: str = "default"):
        """Draw a rectangle."""
        action = DrawAction("rect", x1, y1, x2, y2, color, thickness, user_id=user_id)
        return self.add_action(action)
    
    def add_text(self, x: float, y: float, text: str,
                 color: str = "#ffffff", user_id: str = "default"):
        """Add text annotation."""
        action = DrawAction("text", x, y, text=text, color=color, user_id=user_id)
        return self.add_action(action)
    
    def erase(self, x: float, y: float, radius: float, user_id: str = "default"):
        """Erase at a point."""
        action = DrawAction("erase", x, y, radius, user_id=user_id)
        return self.add_action(action)
    
    def undo(self) -> Dict:
        """Undo last action."""
        if self.actions:
            action = self.actions.pop()
            self.undo_stack.append(action)
            return {"status": "ok", "undone": action.action_type}
        return {"status": "error", "message": "Nothing to undo"}
    
    def redo(self) -> Dict:
        """Redo last undone action."""
        if self.undo_stack:
            action = self.undo_stack.pop()
            self.actions.append(action)
            return {"status": "ok", "redone": action.action_type}
        return {"status": "error", "message": "Nothing to redo"}
    
    def clear(self) -> Dict:
        """Clear the whiteboard."""
        self.actions.clear()
        self.undo_stack.clear()
        return {"status": "ok", "message": "Whiteboard cleared"}
    
    def get_actions(self, since_timestamp: float = 0) -> List[Dict]:
        """Get all actions since a timestamp."""
        actions = [asdict(a) for a in self.actions if a.timestamp > since_timestamp]
        return actions
    
    def export_svg(self, width: int = 1920, height: int = 1080) -> str:
        """Export whiteboard as SVG."""
        svg_parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">']
        svg_parts.append(f'<rect width="100%" height="100%" fill="#1a1a2e"/>')
        
        for action in self.actions:
            if action.action_type == "line":
                svg_parts.append(
                    f'<line x1="{action.x1}" y1="{action.y1}" x2="{action.x2}" y2="{action.y2}" '
                    f'stroke="{action.color}" stroke-width="{action.thickness}"/>'
                )
            elif action.action_type == "circle":
                svg_parts.append(
                    f'<circle cx="{action.x1}" cy="{action.y1}" r="{action.x2}" '
                    f'stroke="{action.color}" stroke-width="{action.thickness}" fill="none"/>'
                )
            elif action.action_type == "rect":
                w = abs(action.x2 - action.x1)
                h = abs(action.y2 - action.y1)
                svg_parts.append(
                    f'<rect x="{min(action.x1, action.x2)}" y="{min(action.y1, action.y2)}" '
                    f'width="{w}" height="{h}" stroke="{action.color}" '
                    f'stroke-width="{action.thickness}" fill="none"/>'
                )
            elif action.action_type == "text":
                svg_parts.append(
                    f'<text x="{action.x1}" y="{action.y1}" fill="{action.color}" '
                    f'font-size="16">{action.text}</text>'
                )
        
        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)
    
    def get_status(self) -> Dict:
        return {
            "action_count": len(self.actions),
            "undo_available": len(self.actions) > 0,
            "redo_available": len(self.undo_stack) > 0
        }


# Global whiteboard
whiteboard = Whiteboard()
