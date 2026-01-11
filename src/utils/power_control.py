"""
Power Control Module for SpaceLink
Provides remote shutdown, restart, lock, sleep, and hibernate functions.
"""
import os
import sys
import subprocess


def shutdown(delay: int = 0, force: bool = False) -> dict:
    """Shutdown the computer."""
    try:
        if sys.platform == "win32":
            cmd = f"shutdown /s /t {delay}"
            if force:
                cmd += " /f"
            os.system(cmd)
        else:
            os.system(f"shutdown -h +{delay // 60}")
        
        return {"status": "ok", "message": f"Shutdown scheduled in {delay}s"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def restart(delay: int = 0, force: bool = False) -> dict:
    """Restart the computer."""
    try:
        if sys.platform == "win32":
            cmd = f"shutdown /r /t {delay}"
            if force:
                cmd += " /f"
            os.system(cmd)
        else:
            os.system(f"shutdown -r +{delay // 60}")
        
        return {"status": "ok", "message": f"Restart scheduled in {delay}s"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def cancel_shutdown() -> dict:
    """Cancel a scheduled shutdown or restart."""
    try:
        if sys.platform == "win32":
            os.system("shutdown /a")
        else:
            os.system("shutdown -c")
        return {"status": "ok", "message": "Shutdown cancelled"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def lock_screen() -> dict:
    """Lock the computer screen."""
    try:
        if sys.platform == "win32":
            import ctypes
            ctypes.windll.user32.LockWorkStation()
        elif sys.platform == "darwin":
            os.system("pmset displaysleepnow")
        else:
            os.system("xdg-screensaver lock")
        
        return {"status": "ok", "message": "Screen locked"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def sleep() -> dict:
    """Put the computer to sleep."""
    try:
        if sys.platform == "win32":
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        elif sys.platform == "darwin":
            os.system("pmset sleepnow")
        else:
            os.system("systemctl suspend")
        
        return {"status": "ok", "message": "Sleep initiated"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def hibernate() -> dict:
    """Hibernate the computer."""
    try:
        if sys.platform == "win32":
            os.system("shutdown /h")
        else:
            os.system("systemctl hibernate")
        
        return {"status": "ok", "message": "Hibernate initiated"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_system_info() -> dict:
    """Get basic system information."""
    import platform
    
    return {
        "platform": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor()
    }
