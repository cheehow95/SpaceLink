"""
Screen Recorder Module for SpaceLink
Records screen to MP4 files with start/stop/pause controls.
"""
import os
import cv2
import time
import threading
import queue
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum

from stream_capture import ScreenCapture


class RecordingState(Enum):
    IDLE = "idle"
    RECORDING = "recording"
    PAUSED = "paused"


@dataclass
class RecordingInfo:
    """Information about a recording."""
    filename: str
    filepath: str
    start_time: datetime
    duration: float
    size: int
    width: int
    height: int
    fps: int


class ScreenRecorder:
    """Records screen to video files."""
    
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir) if output_dir else Path.home() / "SpaceLink_Recordings"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self._screen_capture = ScreenCapture()
        self._state = RecordingState.IDLE
        self._writer: Optional[cv2.VideoWriter] = None
        self._current_recording: Optional[RecordingInfo] = None
        self._recording_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        
        # Recording settings
        self._fps = 30
        self._codec = "mp4v"  # or "avc1" for H.264
        self._quality = 0.7  # Scale factor
        
        print(f"[Recorder] Output directory: {self.output_dir}")
    
    def start_recording(self, filename: Optional[str] = None, fps: int = 30) -> Dict:
        """Start a new recording."""
        if self._state != RecordingState.IDLE:
            return {"status": "error", "message": f"Already in state: {self._state.value}"}
        
        self._fps = fps
        
        # Generate filename
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.mp4"
        
        if not filename.endswith(".mp4"):
            filename += ".mp4"
        
        filepath = self.output_dir / filename
        
        # Get screen dimensions
        frame = self._screen_capture.get_frame()
        height, width = frame.shape[:2]
        
        # Apply quality scaling
        if self._quality < 1.0:
            width = int(width * self._quality)
            height = int(height * self._quality)
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*self._codec)
        self._writer = cv2.VideoWriter(str(filepath), fourcc, fps, (width, height))
        
        if not self._writer.isOpened():
            return {"status": "error", "message": "Failed to create video writer"}
        
        # Create recording info
        self._current_recording = RecordingInfo(
            filename=filename,
            filepath=str(filepath),
            start_time=datetime.now(),
            duration=0,
            size=0,
            width=width,
            height=height,
            fps=fps
        )
        
        # Start recording thread
        self._stop_event.clear()
        self._pause_event.set()  # Not paused
        self._state = RecordingState.RECORDING
        self._recording_thread = threading.Thread(target=self._record_loop, daemon=True)
        self._recording_thread.start()
        
        print(f"[Recorder] Started: {filename}")
        
        return {
            "status": "ok",
            "message": "Recording started",
            "filename": filename,
            "resolution": f"{width}x{height}",
            "fps": fps
        }
    
    def _record_loop(self):
        """Recording loop running in background thread."""
        frame_interval = 1.0 / self._fps
        frame_count = 0
        
        while not self._stop_event.is_set():
            start_time = time.time()
            
            # Check if paused
            if not self._pause_event.is_set():
                time.sleep(0.1)
                continue
            
            try:
                # Capture frame
                frame = self._screen_capture.get_frame()
                
                # Resize if needed
                if self._quality < 1.0:
                    width = int(frame.shape[1] * self._quality)
                    height = int(frame.shape[0] * self._quality)
                    frame = cv2.resize(frame, (width, height))
                
                # Write frame
                self._writer.write(frame)
                frame_count += 1
                
                # Update duration
                if self._current_recording:
                    self._current_recording.duration = frame_count / self._fps
                
            except Exception as e:
                print(f"[Recorder] Frame error: {e}")
            
            # Maintain frame rate
            elapsed = time.time() - start_time
            sleep_time = max(0, frame_interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        # Finalize
        if self._writer:
            self._writer.release()
            self._writer = None
        
        # Update file size
        if self._current_recording:
            try:
                self._current_recording.size = os.path.getsize(self._current_recording.filepath)
            except:
                pass
        
        print(f"[Recorder] Stopped. Frames: {frame_count}, Duration: {self._current_recording.duration:.1f}s")
    
    def pause_recording(self) -> Dict:
        """Pause the current recording."""
        if self._state != RecordingState.RECORDING:
            return {"status": "error", "message": "Not recording"}
        
        self._pause_event.clear()
        self._state = RecordingState.PAUSED
        
        return {"status": "ok", "message": "Recording paused"}
    
    def resume_recording(self) -> Dict:
        """Resume a paused recording."""
        if self._state != RecordingState.PAUSED:
            return {"status": "error", "message": "Not paused"}
        
        self._pause_event.set()
        self._state = RecordingState.RECORDING
        
        return {"status": "ok", "message": "Recording resumed"}
    
    def stop_recording(self) -> Dict:
        """Stop the current recording."""
        if self._state == RecordingState.IDLE:
            return {"status": "error", "message": "Not recording"}
        
        # Signal stop
        self._stop_event.set()
        self._pause_event.set()  # Unblock if paused
        
        # Wait for thread
        if self._recording_thread:
            self._recording_thread.join(timeout=5.0)
        
        self._state = RecordingState.IDLE
        
        result = {
            "status": "ok",
            "message": "Recording stopped"
        }
        
        if self._current_recording:
            result.update({
                "filename": self._current_recording.filename,
                "filepath": self._current_recording.filepath,
                "duration": self._current_recording.duration,
                "size": self._current_recording.size
            })
        
        self._current_recording = None
        
        return result
    
    def get_status(self) -> Dict:
        """Get current recording status."""
        status = {
            "state": self._state.value,
            "output_dir": str(self.output_dir)
        }
        
        if self._current_recording:
            status.update({
                "filename": self._current_recording.filename,
                "duration": self._current_recording.duration,
                "resolution": f"{self._current_recording.width}x{self._current_recording.height}",
                "fps": self._current_recording.fps
            })
        
        return status
    
    def list_recordings(self) -> Dict:
        """List available recordings."""
        recordings = []
        
        try:
            for file in self.output_dir.glob("*.mp4"):
                stat = file.stat()
                recordings.append({
                    "filename": file.name,
                    "filepath": str(file),
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            
            # Sort by modification time (newest first)
            recordings.sort(key=lambda x: x["modified"], reverse=True)
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
        
        return {
            "status": "ok",
            "count": len(recordings),
            "recordings": recordings
        }
    
    def delete_recording(self, filename: str) -> Dict:
        """Delete a recording file."""
        try:
            filepath = self.output_dir / filename
            if filepath.exists():
                filepath.unlink()
                return {"status": "ok", "message": f"Deleted: {filename}"}
            return {"status": "error", "message": "File not found"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def set_quality(self, scale: float = 1.0, codec: str = "mp4v") -> Dict:
        """Set recording quality settings."""
        self._quality = max(0.25, min(1.0, scale))
        self._codec = codec
        return {
            "status": "ok",
            "scale": self._quality,
            "codec": self._codec
        }


# Global instance
screen_recorder = ScreenRecorder()
