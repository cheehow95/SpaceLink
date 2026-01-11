from core.input_control import CMD_KEY_TYPE, CMD_MOUSE_CLICK, CMD_SCROLL, CMD_KEY_PRESS, CMD_MOUSE_MOVE, CMD_MOUSE_DRAG
import subprocess
import re


class AIAgent:
    def __init__(self):
        print("AI Agent Initialized (Enhanced Rule-based Mode)")
        
        # Common key mappings for natural language
        self.key_mappings = {
            "enter": "enter",
            "return": "enter",
            "escape": "esc",
            "esc": "esc",
            "backspace": "backspace",
            "delete": "delete",
            "tab": "tab",
            "space": "space",
            "up": "up",
            "down": "down",
            "left": "left",
            "right": "right",
            "home": "home",
            "end": "end",
            "pageup": "pageup",
            "pagedown": "pagedown",
            "f1": "f1", "f2": "f2", "f3": "f3", "f4": "f4",
            "f5": "f5", "f6": "f6", "f7": "f7", "f8": "f8",
            "f9": "f9", "f10": "f10", "f11": "f11", "f12": "f12",
        }
        
        # Hotkey patterns
        self.hotkey_patterns = {
            "copy": ["ctrl", "c"],
            "paste": ["ctrl", "v"],
            "cut": ["ctrl", "x"],
            "undo": ["ctrl", "z"],
            "redo": ["ctrl", "y"],
            "save": ["ctrl", "s"],
            "select all": ["ctrl", "a"],
            "find": ["ctrl", "f"],
            "new tab": ["ctrl", "t"],
            "close tab": ["ctrl", "w"],
            "switch window": ["alt", "tab"],
            "task manager": ["ctrl", "shift", "esc"],
            "desktop": ["win", "d"],
            "lock": ["win", "l"],
            "run": ["win", "r"],
            "screenshot": ["win", "shift", "s"],
        }

    def process_command(self, prompt: str) -> dict:
        """
        Parses natural language prompt into a structured command.
        Enhanced with more command patterns.
        """
        prompt_lower = prompt.lower().strip()
        
        # Rule 1: Typing
        if prompt_lower.startswith("type "):
            text_to_type = prompt[5:]  # preserve original case
            return {
                "type": CMD_KEY_TYPE,
                "data": {"text": text_to_type}
            }
        
        # Rule 2: Press Key
        if prompt_lower.startswith("press "):
            key = prompt_lower[6:].strip()
            # Check if it's a mapped key
            if key in self.key_mappings:
                return {
                    "type": CMD_KEY_PRESS,
                    "data": {"key": self.key_mappings[key]}
                }
            # Otherwise try to use the key directly
            return {
                "type": CMD_KEY_PRESS,
                "data": {"key": key}
            }
        
        # Rule 3: Hotkeys (ctrl+c style)
        hotkey_match = re.match(r'^(ctrl|alt|shift|win)[\+\-\s]+(.*)', prompt_lower)
        if hotkey_match:
            modifier = hotkey_match.group(1)
            key = hotkey_match.group(2).strip()
            return {
                "type": "hotkey",
                "data": {"keys": [modifier, key]}
            }
        
        # Rule 4: Named Hotkeys (copy, paste, etc.)
        for name, keys in self.hotkey_patterns.items():
            if name in prompt_lower:
                return {
                    "type": "hotkey",
                    "data": {"keys": keys}
                }
        
        # Rule 5: Clicking
        if "click" in prompt_lower:
            button = "left"
            if "right" in prompt_lower:
                button = "right"
            elif "middle" in prompt_lower:
                button = "middle"
            elif "double" in prompt_lower:
                return {
                    "type": "double_click",
                    "data": {"button": "left"}
                }
            return {
                "type": CMD_MOUSE_CLICK,
                "data": {"button": button}
            }

        # Rule 6: Scrolling
        if "scroll" in prompt_lower:
            amount = 200  # default
            if "up" in prompt_lower:
                pass
            elif "down" in prompt_lower:
                amount = -200
            elif "left" in prompt_lower:
                return {
                    "type": "scroll_horizontal",
                    "data": {"amount": -200}
                }
            elif "right" in prompt_lower:
                return {
                    "type": "scroll_horizontal",
                    "data": {"amount": 200}
                }
            return {
                "type": CMD_SCROLL,
                "data": {"amount": amount}
            }
        
        # Rule 7: Move mouse to position
        move_match = re.match(r'move\s*(?:to|mouse)?\s*(\d+)\s*[,\s]\s*(\d+)', prompt_lower)
        if move_match:
            x = int(move_match.group(1))
            y = int(move_match.group(2))
            return {
                "type": CMD_MOUSE_MOVE,
                "data": {"x": x, "y": y}
            }
        
        # Rule 8: Open application (Windows)
        if prompt_lower.startswith("open "):
            app_name = prompt[5:].strip()
            return {
                "type": "open_app",
                "data": {"app": app_name}
            }
        
        # Rule 9: Screenshot
        if "screenshot" in prompt_lower or "screen shot" in prompt_lower:
            return {
                "type": "hotkey",
                "data": {"keys": ["win", "shift", "s"]}
            }
        
        # Rule 10: Minimize/Maximize window
        if "minimize" in prompt_lower:
            return {
                "type": "hotkey",
                "data": {"keys": ["win", "down"]}
            }
        if "maximize" in prompt_lower:
            return {
                "type": "hotkey",
                "data": {"keys": ["win", "up"]}
            }
        
        # Rule 11: Drag from position to position
        drag_match = re.match(r'drag\s*(?:from)?\s*(\d+)\s*[,\s]\s*(\d+)\s*to\s*(\d+)\s*[,\s]\s*(\d+)', prompt_lower)
        if drag_match:
            return {
                "type": CMD_MOUSE_DRAG,
                "data": {
                    "from_x": int(drag_match.group(1)),
                    "from_y": int(drag_match.group(2)),
                    "to_x": int(drag_match.group(3)),
                    "to_y": int(drag_match.group(4))
                }
            }
        
        # Rule 12: Window snap commands
        if "snap" in prompt_lower or "move window" in prompt_lower:
            if "left" in prompt_lower:
                return {"type": "hotkey", "data": {"keys": ["win", "left"]}}
            elif "right" in prompt_lower:
                return {"type": "hotkey", "data": {"keys": ["win", "right"]}}
            elif "up" in prompt_lower or "top" in prompt_lower:
                return {"type": "hotkey", "data": {"keys": ["win", "up"]}}
            elif "down" in prompt_lower or "bottom" in prompt_lower:
                return {"type": "hotkey", "data": {"keys": ["win", "down"]}}
        
        # Rule 13: New document/file shortcuts
        if "new document" in prompt_lower or "new file" in prompt_lower:
            return {"type": "hotkey", "data": {"keys": ["ctrl", "n"]}}
        
        if "close window" in prompt_lower or "close app" in prompt_lower:
            return {"type": "hotkey", "data": {"keys": ["alt", "f4"]}}
        
        # Fallback / Unknown
        return {"status": "error", "message": f"I didn't understand: '{prompt}'"}
