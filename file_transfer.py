"""
File Transfer Module for SpaceLink
Enables file upload/download between PC and clients.
"""
import os
import hashlib
import base64
import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime

# Default directory for file transfers
DEFAULT_TRANSFER_DIR = Path.home() / "SpaceLink_Transfers"


class FileTransferManager:
    """Manages file transfer operations."""
    
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir) if base_dir else DEFAULT_TRANSFER_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._current_dir = self.base_dir
        print(f"[FileTransfer] Base directory: {self.base_dir}")
    
    def set_current_dir(self, path: str) -> dict:
        """Change current directory for browsing."""
        try:
            new_path = Path(path).resolve()
            if new_path.is_dir():
                self._current_dir = new_path
                return {"status": "ok", "path": str(new_path)}
            return {"status": "error", "message": "Not a directory"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def list_files(self, path: Optional[str] = None) -> dict:
        """List files in the specified or current directory."""
        try:
            target_dir = Path(path) if path else self._current_dir
            target_dir = target_dir.resolve()
            
            if not target_dir.is_dir():
                return {"status": "error", "message": "Not a directory"}
            
            items = []
            for item in target_dir.iterdir():
                try:
                    stat = item.stat()
                    items.append({
                        "name": item.name,
                        "path": str(item),
                        "is_dir": item.is_dir(),
                        "size": stat.st_size if item.is_file() else 0,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                except (PermissionError, OSError):
                    continue
            
            # Sort: directories first, then files
            items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
            
            return {
                "status": "ok",
                "path": str(target_dir),
                "parent": str(target_dir.parent) if target_dir != target_dir.parent else None,
                "items": items
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_drives(self) -> dict:
        """List available drives (Windows) or mount points."""
        drives = []
        
        if os.name == 'nt':  # Windows
            import string
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    try:
                        # Get drive info
                        total, used, free = 0, 0, 0
                        try:
                            import shutil
                            usage = shutil.disk_usage(drive)
                            total, used, free = usage.total, usage.used, usage.free
                        except:
                            pass
                        
                        drives.append({
                            "name": drive,
                            "path": drive,
                            "total": total,
                            "free": free
                        })
                    except:
                        pass
        else:  # Unix-like
            drives.append({"name": "/", "path": "/", "total": 0, "free": 0})
            # Add common mount points
            for mount in ["/home", "/mnt", "/media"]:
                if os.path.isdir(mount):
                    drives.append({"name": mount, "path": mount, "total": 0, "free": 0})
        
        return {"status": "ok", "drives": drives}
    
    def read_file(self, path: str, chunk_size: int = 1024 * 1024) -> dict:
        """Read a file and return its contents (for small files) or info for streaming."""
        try:
            file_path = Path(path).resolve()
            
            if not file_path.is_file():
                return {"status": "error", "message": "File not found"}
            
            file_size = file_path.stat().st_size
            
            # For small files (< 10MB), return base64 encoded
            if file_size < 10 * 1024 * 1024:
                with open(file_path, 'rb') as f:
                    content = base64.b64encode(f.read()).decode('utf-8')
                return {
                    "status": "ok",
                    "name": file_path.name,
                    "size": file_size,
                    "content": content,
                    "encoding": "base64"
                }
            else:
                # For large files, return info for chunked download
                return {
                    "status": "ok",
                    "name": file_path.name,
                    "size": file_size,
                    "chunks": (file_size + chunk_size - 1) // chunk_size,
                    "chunk_size": chunk_size,
                    "use_streaming": True
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def read_file_chunk(self, path: str, chunk_index: int, chunk_size: int = 1024 * 1024) -> dict:
        """Read a specific chunk of a file."""
        try:
            file_path = Path(path).resolve()
            
            if not file_path.is_file():
                return {"status": "error", "message": "File not found"}
            
            file_size = file_path.stat().st_size
            offset = chunk_index * chunk_size
            
            if offset >= file_size:
                return {"status": "error", "message": "Chunk index out of range"}
            
            with open(file_path, 'rb') as f:
                f.seek(offset)
                data = f.read(chunk_size)
            
            return {
                "status": "ok",
                "chunk_index": chunk_index,
                "chunk_size": len(data),
                "content": base64.b64encode(data).decode('utf-8'),
                "is_last": offset + len(data) >= file_size
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def write_file(self, path: str, content: str, encoding: str = "base64", append: bool = False) -> dict:
        """Write content to a file."""
        try:
            file_path = Path(path).resolve()
            
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Decode content
            if encoding == "base64":
                data = base64.b64decode(content)
            else:
                data = content.encode('utf-8')
            
            # Write file
            mode = 'ab' if append else 'wb'
            with open(file_path, mode) as f:
                f.write(data)
            
            return {
                "status": "ok",
                "path": str(file_path),
                "size": file_path.stat().st_size
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def delete_file(self, path: str) -> dict:
        """Delete a file or empty directory."""
        try:
            target = Path(path).resolve()
            
            if target.is_file():
                target.unlink()
                return {"status": "ok", "message": f"Deleted file: {target.name}"}
            elif target.is_dir():
                target.rmdir()  # Only works if empty
                return {"status": "ok", "message": f"Deleted directory: {target.name}"}
            else:
                return {"status": "error", "message": "Path not found"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def create_directory(self, path: str) -> dict:
        """Create a new directory."""
        try:
            dir_path = Path(path).resolve()
            dir_path.mkdir(parents=True, exist_ok=True)
            return {"status": "ok", "path": str(dir_path)}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_file_hash(self, path: str) -> dict:
        """Get SHA-256 hash of a file."""
        try:
            file_path = Path(path).resolve()
            
            if not file_path.is_file():
                return {"status": "error", "message": "File not found"}
            
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256.update(chunk)
            
            return {
                "status": "ok",
                "path": str(file_path),
                "hash": sha256.hexdigest()
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}


# Global instance
file_manager = FileTransferManager()
