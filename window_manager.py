"""
Window Manager Module for SpaceLink
List, focus, minimize, maximize, and close windows.
"""
import sys
from typing import List, Dict

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes
    
    user32 = ctypes.windll.user32
    
    # Window enumeration callback
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)


def get_windows() -> List[Dict]:
    """Get list of all visible windows."""
    windows = []
    
    if sys.platform == "win32":
        def callback(hwnd, lParam):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    title = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, title, length + 1)
                    if title.value.strip():
                        windows.append({
                            "hwnd": hwnd,
                            "title": title.value[:50],
                            "is_minimized": user32.IsIconic(hwnd),
                            "is_maximized": user32.IsZoomed(hwnd)
                        })
            return True
        
        user32.EnumWindows(EnumWindowsProc(callback), 0)
    else:
        # Placeholder for Linux/Mac
        windows.append({"hwnd": 0, "title": "Window list not supported on this platform"})
    
    return windows[:20]  # Limit to 20 windows


def focus_window(hwnd: int) -> dict:
    """Bring a window to the foreground."""
    if sys.platform == "win32":
        try:
            # Restore if minimized
            if user32.IsIconic(hwnd):
                user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            
            # Bring to foreground
            user32.SetForegroundWindow(hwnd)
            return {"status": "ok", "message": "Window focused"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    return {"status": "error", "message": "Not supported on this platform"}


def minimize_window(hwnd: int) -> dict:
    """Minimize a window."""
    if sys.platform == "win32":
        try:
            user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE
            return {"status": "ok", "message": "Window minimized"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    return {"status": "error", "message": "Not supported"}


def maximize_window(hwnd: int) -> dict:
    """Maximize a window."""
    if sys.platform == "win32":
        try:
            user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
            return {"status": "ok", "message": "Window maximized"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    return {"status": "error", "message": "Not supported"}


def close_window(hwnd: int) -> dict:
    """Close a window."""
    if sys.platform == "win32":
        try:
            user32.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE
            return {"status": "ok", "message": "Window closed"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    return {"status": "error", "message": "Not supported"}
