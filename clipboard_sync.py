"""
Clipboard Sync Module for SpaceLink
Enables bidirectional clipboard sharing between PC and clients.
"""
import base64
import io
import threading
import time
from typing import Optional, Any
from dataclasses import dataclass
from datetime import datetime

# Try to import clipboard libraries
try:
    import pyperclip
    CLIPBOARD_BACKEND = "pyperclip"
except ImportError:
    CLIPBOARD_BACKEND = None

# Try to import PIL for image support
try:
    from PIL import Image, ImageGrab
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


@dataclass
class ClipboardContent:
    """Represents clipboard content."""
    content_type: str  # "text", "image", "files", "empty"
    data: Any
    timestamp: datetime


class ClipboardManager:
    """Manages clipboard operations and synchronization."""
    
    def __init__(self):
        self._last_content: Optional[ClipboardContent] = None
        self._sync_enabled = False
        self._sync_interval = 1.0  # seconds
        self._sync_thread: Optional[threading.Thread] = None
        self._callbacks = []
        print(f"[Clipboard] Backend: {CLIPBOARD_BACKEND}, PIL: {HAS_PIL}")
    
    def get_clipboard(self) -> dict:
        """Get current clipboard content."""
        try:
            result = {"status": "ok", "content_type": "empty", "data": None}
            
            # Try to get image first (Windows)
            if HAS_PIL:
                try:
                    img = ImageGrab.grabclipboard()
                    if img is not None and isinstance(img, Image.Image):
                        # Convert image to base64 PNG
                        buffer = io.BytesIO()
                        img.save(buffer, format='PNG')
                        img_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
                        result = {
                            "status": "ok",
                            "content_type": "image",
                            "data": img_data,
                            "format": "png",
                            "width": img.width,
                            "height": img.height
                        }
                        return result
                    elif img is not None and isinstance(img, list):
                        # File list (paths)
                        result = {
                            "status": "ok",
                            "content_type": "files",
                            "data": img
                        }
                        return result
                except Exception as e:
                    pass  # Fall through to text
            
            # Try to get text
            if CLIPBOARD_BACKEND == "pyperclip":
                try:
                    text = pyperclip.paste()
                    if text:
                        result = {
                            "status": "ok",
                            "content_type": "text",
                            "data": text
                        }
                except Exception as e:
                    result = {"status": "error", "message": str(e)}
            else:
                # Fallback: use win32clipboard on Windows
                try:
                    import win32clipboard
                    win32clipboard.OpenClipboard()
                    try:
                        text = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                        result = {
                            "status": "ok",
                            "content_type": "text",
                            "data": text
                        }
                    except:
                        pass
                    finally:
                        win32clipboard.CloseClipboard()
                except ImportError:
                    result = {"status": "error", "message": "No clipboard backend available"}
            
            return result
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def set_clipboard(self, content_type: str, data: Any) -> dict:
        """Set clipboard content."""
        try:
            if content_type == "text":
                if CLIPBOARD_BACKEND == "pyperclip":
                    pyperclip.copy(data)
                else:
                    try:
                        import win32clipboard
                        win32clipboard.OpenClipboard()
                        win32clipboard.EmptyClipboard()
                        win32clipboard.SetClipboardText(data, win32clipboard.CF_UNICODETEXT)
                        win32clipboard.CloseClipboard()
                    except ImportError:
                        return {"status": "error", "message": "No clipboard backend available"}
                
                return {"status": "ok", "message": "Text copied to clipboard"}
            
            elif content_type == "image" and HAS_PIL:
                # Decode base64 image and copy to clipboard
                img_data = base64.b64decode(data)
                img = Image.open(io.BytesIO(img_data))
                
                # Copy image to clipboard (Windows-specific)
                try:
                    import win32clipboard
                    from io import BytesIO
                    
                    output = BytesIO()
                    img.convert("RGB").save(output, "BMP")
                    data = output.getvalue()[14:]  # Remove BMP header
                    output.close()
                    
                    win32clipboard.OpenClipboard()
                    win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                    win32clipboard.CloseClipboard()
                    
                    return {"status": "ok", "message": "Image copied to clipboard"}
                except ImportError:
                    return {"status": "error", "message": "win32clipboard not available for image copy"}
            
            else:
                return {"status": "error", "message": f"Unsupported content type: {content_type}"}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def start_sync(self, callback=None):
        """Start clipboard sync monitoring."""
        if self._sync_enabled:
            return
        
        if callback:
            self._callbacks.append(callback)
        
        self._sync_enabled = True
        self._sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._sync_thread.start()
        print("[Clipboard] Sync started")
    
    def stop_sync(self):
        """Stop clipboard sync monitoring."""
        self._sync_enabled = False
        if self._sync_thread:
            self._sync_thread.join(timeout=2.0)
        print("[Clipboard] Sync stopped")
    
    def _sync_loop(self):
        """Monitor clipboard for changes."""
        while self._sync_enabled:
            try:
                current = self.get_clipboard()
                if current.get("status") == "ok":
                    content = ClipboardContent(
                        content_type=current.get("content_type", "empty"),
                        data=current.get("data"),
                        timestamp=datetime.now()
                    )
                    
                    # Check if content changed
                    if self._content_changed(content):
                        self._last_content = content
                        for callback in self._callbacks:
                            try:
                                callback(current)
                            except Exception as e:
                                print(f"[Clipboard] Callback error: {e}")
            
            except Exception as e:
                print(f"[Clipboard] Sync error: {e}")
            
            time.sleep(self._sync_interval)
    
    def _content_changed(self, new_content: ClipboardContent) -> bool:
        """Check if clipboard content has changed."""
        if self._last_content is None:
            return True
        
        if new_content.content_type != self._last_content.content_type:
            return True
        
        # For text, compare directly (limited to avoid memory issues)
        if new_content.content_type == "text":
            old_data = str(self._last_content.data)[:10000]
            new_data = str(new_content.data)[:10000]
            return old_data != new_data
        
        # For images, we'd need to compare hashes (simplified: assume changed)
        return True
    
    def add_change_callback(self, callback):
        """Add a callback for clipboard changes."""
        self._callbacks.append(callback)
    
    def remove_change_callback(self, callback):
        """Remove a clipboard change callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)


# Global instance
clipboard_manager = ClipboardManager()
