"""
Remote Printing Module for SpaceLink v4.1
Print documents on remote PC's printers.
"""
import os
import sys
import tempfile
from typing import List, Dict, Optional

if sys.platform == "win32":
    try:
        import win32print
        import win32api
        PRINT_AVAILABLE = True
    except ImportError:
        PRINT_AVAILABLE = False
else:
    PRINT_AVAILABLE = False


def get_printers() -> List[Dict]:
    """Get list of available printers."""
    printers = []
    
    if sys.platform == "win32" and PRINT_AVAILABLE:
        try:
            default = win32print.GetDefaultPrinter()
            for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS):
                printers.append({
                    "name": printer[2],
                    "is_default": printer[2] == default,
                    "status": "ready"
                })
        except Exception as e:
            print(f"[Print] Error listing printers: {e}")
    else:
        # Fallback for other platforms
        printers.append({"name": "Default Printer", "is_default": True, "status": "unknown"})
    
    return printers


def get_default_printer() -> str:
    """Get the default printer name."""
    if sys.platform == "win32" and PRINT_AVAILABLE:
        try:
            return win32print.GetDefaultPrinter()
        except:
            pass
    return "Default"


def print_file(filepath: str, printer_name: Optional[str] = None) -> Dict:
    """Print a file to a printer."""
    if not os.path.exists(filepath):
        return {"status": "error", "message": "File not found"}
    
    if sys.platform == "win32" and PRINT_AVAILABLE:
        try:
            if printer_name is None:
                printer_name = get_default_printer()
            
            # Use ShellExecute for most file types
            win32api.ShellExecute(0, "print", filepath, None, ".", 0)
            
            return {
                "status": "ok",
                "message": f"Printing {os.path.basename(filepath)} to {printer_name}"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    return {"status": "error", "message": "Printing not available on this platform"}


def print_text(text: str, printer_name: Optional[str] = None) -> Dict:
    """Print raw text."""
    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    temp_file.write(text)
    temp_file.close()
    
    result = print_file(temp_file.name, printer_name)
    
    # Clean up after a delay (let print spooler grab the file)
    import threading
    def cleanup():
        import time
        time.sleep(5)
        try:
            os.remove(temp_file.name)
        except:
            pass
    threading.Thread(target=cleanup, daemon=True).start()
    
    return result


def print_url(url: str) -> Dict:
    """Open URL for printing (uses browser print dialog)."""
    import webbrowser
    try:
        webbrowser.open(url)
        return {"status": "ok", "message": "Opened URL for printing"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_status() -> Dict:
    """Get print module status."""
    return {
        "available": PRINT_AVAILABLE,
        "printers": get_printers(),
        "default": get_default_printer()
    }
