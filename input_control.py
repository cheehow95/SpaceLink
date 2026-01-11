import pyautogui
import subprocess
import os

# Disable pyautogui fail-safe for remote control (can enable for safety)
# pyautogui.FAILSAFE = True 
pyautogui.PAUSE = 0.05  # Small pause between actions

CMD_MOUSE_MOVE = "mouse_move"
CMD_MOUSE_MOVE_RELATIVE = "mouse_move_relative"
CMD_MOUSE_CLICK = "mouse_click"
CMD_KEY_TYPE = "key_type"
CMD_KEY_PRESS = "key_press"
CMD_SCROLL = "scroll"
CMD_HOTKEY = "hotkey"
CMD_DOUBLE_CLICK = "double_click"
CMD_SCROLL_HORIZONTAL = "scroll_horizontal"
CMD_OPEN_APP = "open_app"
CMD_MOUSE_DOWN = "mouse_down"
CMD_MOUSE_UP = "mouse_up"
CMD_MOUSE_DRAG = "mouse_drag"


def execute_command(command_json: dict):
    """
    Parses and executes a command dictionary.
    
    Structure expected:
    {
        "type": "command_type",
        "data": { ...args... }
    }
    """
    cmd_type = command_json.get("type")
    data = command_json.get("data", {})
    
    try:
        if cmd_type == CMD_MOUSE_MOVE:
            screen_w, screen_h = pyautogui.size()
            
            if "nx" in data and "ny" in data:
                # Normalized coordinates 0.0 to 1.0
                x = int(data["nx"] * screen_w)
                y = int(data["ny"] * screen_h)
                pyautogui.moveTo(x, y)
            elif "x" in data and "y" in data:
                x = data["x"]
                y = data["y"]
                pyautogui.moveTo(x, y)
        
        elif cmd_type == CMD_MOUSE_MOVE_RELATIVE:
            # Relative mouse movement (for gamepad)
            dx = data.get("dx", 0)
            dy = data.get("dy", 0)
            pyautogui.moveRel(dx, dy)
                
        elif cmd_type == CMD_MOUSE_CLICK:
            button = data.get("button", "left")
            clicks = data.get("clicks", 1)
            pyautogui.click(button=button, clicks=clicks)
            
        elif cmd_type == CMD_DOUBLE_CLICK:
            button = data.get("button", "left")
            pyautogui.doubleClick(button=button)
            
        elif cmd_type == CMD_SCROLL:
            amount = data.get("amount", 0)
            pyautogui.scroll(amount)
            
        elif cmd_type == CMD_SCROLL_HORIZONTAL:
            amount = data.get("amount", 0)
            pyautogui.hscroll(amount)

        elif cmd_type == CMD_KEY_TYPE:
            text = data.get("text")
            if text:
                pyautogui.write(text, interval=0.02)
                
        elif cmd_type == CMD_KEY_PRESS:
            key = data.get("key")
            if key:
                pyautogui.press(key)
                
        elif cmd_type == CMD_HOTKEY:
            keys = data.get("keys", [])
            if keys:
                pyautogui.hotkey(*keys)
                
        elif cmd_type == CMD_OPEN_APP:
            app = data.get("app", "")
            if app:
                # Try to open the app using Windows start command
                try:
                    subprocess.Popen(f'start "" "{app}"', shell=True)
                except:
                    # Fallback: try running directly
                    subprocess.Popen(app, shell=True)
        
        elif cmd_type == CMD_MOUSE_DOWN:
            button = data.get("button", "left")
            pyautogui.mouseDown(button=button)
            
        elif cmd_type == CMD_MOUSE_UP:
            button = data.get("button", "left")
            pyautogui.mouseUp(button=button)
            
        elif cmd_type == CMD_MOUSE_DRAG:
            screen_w, screen_h = pyautogui.size()
            # Support normalized coordinates (0-1) or delta movements
            if "nx" in data and "ny" in data:
                x = int(data["nx"] * screen_w)
                y = int(data["ny"] * screen_h)
                current_x, current_y = pyautogui.position()
                pyautogui.drag(x - current_x, y - current_y, duration=0.1)
            elif "dx" in data and "dy" in data:
                pyautogui.drag(data["dx"], data["dy"], duration=0.1)
            elif "from_x" in data and "to_x" in data:
                # Absolute coordinates drag
                pyautogui.moveTo(data["from_x"], data["from_y"])
                pyautogui.drag(data["to_x"] - data["from_x"], data["to_y"] - data["from_y"], duration=0.2)
                    
        else:
            print(f"[Input] Unknown command type: {cmd_type}")
            return {"status": "error", "message": f"Unknown command: {cmd_type}"}
            
        print(f"[Input] Executed: {cmd_type}")
        return {"status": "ok", "executed": cmd_type}
        
    except Exception as e:
        print(f"[Input] Error executing {cmd_type}: {e}")
        return {"status": "error", "message": str(e)}
