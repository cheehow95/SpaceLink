import mss
import cv2
import numpy as np
import time
from typing import List, Dict, Optional


class ScreenCapture:
    """
    Screen capture with multi-monitor support.
    """
    
    def __init__(self, monitor_index: int = 1):
        """
        Initialize screen capture.
        
        Args:
            monitor_index: 1-based monitor index (0 = all monitors combined, 1 = primary, etc.)
        """
        self._monitor_index = monitor_index
        self._monitors_info: List[Dict] = []
        
        # Get initial monitor info
        self._refresh_monitors()
        
        # Select the specified monitor
        self.select_monitor(monitor_index)
    
    def _refresh_monitors(self):
        """Refresh the list of available monitors."""
        with mss.mss() as sct:
            self._monitors_info = []
            for i, mon in enumerate(sct.monitors):
                self._monitors_info.append({
                    "index": i,
                    "left": mon["left"],
                    "top": mon["top"],
                    "width": mon["width"],
                    "height": mon["height"],
                    "is_all": i == 0,
                    "name": "All Monitors" if i == 0 else f"Monitor {i}"
                })
    
    def enumerate_monitors(self) -> List[Dict]:
        """
        Get list of available monitors.
        
        Returns:
            List of monitor info dicts with index, dimensions, and name
        """
        self._refresh_monitors()
        return [
            {
                "index": m["index"],
                "name": m["name"],
                "width": m["width"],
                "height": m["height"],
                "position": {"x": m["left"], "y": m["top"]},
                "is_primary": m["index"] == 1,
                "is_virtual_desktop": m["is_all"],
                "selected": m["index"] == self._monitor_index
            }
            for m in self._monitors_info
        ]
    
    def select_monitor(self, monitor_index: int) -> Dict:
        """
        Select a monitor for capture.
        
        Args:
            monitor_index: 0 for all monitors, 1+ for specific monitor
        
        Returns:
            Status dict with monitor info
        """
        self._refresh_monitors()
        
        if monitor_index < 0 or monitor_index >= len(self._monitors_info):
            return {"status": "error", "message": f"Invalid monitor index: {monitor_index}"}
        
        self._monitor_index = monitor_index
        mon = self._monitors_info[monitor_index]
        
        self.monitor = {
            "left": mon["left"],
            "top": mon["top"],
            "width": mon["width"],
            "height": mon["height"]
        }
        self.width = mon["width"]
        self.height = mon["height"]
        
        print(f"[Capture] Selected monitor {monitor_index}: {mon['name']} ({mon['width']}x{mon['height']})")
        
        return {
            "status": "ok",
            "monitor_index": monitor_index,
            "name": mon["name"],
            "width": mon["width"],
            "height": mon["height"]
        }
    
    def get_current_monitor(self) -> Dict:
        """Get info about currently selected monitor."""
        if self._monitor_index < len(self._monitors_info):
            mon = self._monitors_info[self._monitor_index]
            return {
                "index": mon["index"],
                "name": mon["name"],
                "width": mon["width"],
                "height": mon["height"]
            }
        return {"index": 1, "name": "Primary", "width": 1920, "height": 1080}
    
    def get_virtual_desktop(self) -> Dict:
        """
        Get dimensions of the virtual desktop (all monitors combined).
        """
        self._refresh_monitors()
        
        if len(self._monitors_info) > 0:
            all_mon = self._monitors_info[0]
            return {
                "width": all_mon["width"],
                "height": all_mon["height"],
                "left": all_mon["left"],
                "top": all_mon["top"]
            }
        return {"width": 1920, "height": 1080, "left": 0, "top": 0}
    
    @property
    def monitor_count(self) -> int:
        """Get number of physical monitors (excluding virtual desktop)."""
        return max(0, len(self._monitors_info) - 1)
        
    def get_frame(self):
        """Capture current frame from selected monitor."""
        # Create fresh mss instance each time (avoids threading issues)
        with mss.mss() as sct:
            # Capture screen
            screenshot = sct.grab(self.monitor)
            
            # Convert to numpy array (BGRA)
            img = np.array(screenshot)
            
            # Drop alpha channel (BGRA -> BGR)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            return img
    
    def get_frame_region(self, left: int, top: int, width: int, height: int):
        """Capture a specific region of the screen."""
        region = {"left": left, "top": top, "width": width, "height": height}
        with mss.mss() as sct:
            screenshot = sct.grab(region)
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            return img

    def generate_jpeg_stream(self, quality=50, resize_factor=0.5):
        """Yields MJPEG frames"""
        while True:
            try:
                frame = self.get_frame()
                
                # Resize for performance constraint if needed
                if resize_factor != 1.0:
                    width = int(frame.shape[1] * resize_factor)
                    height = int(frame.shape[0] * resize_factor)
                    frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)

                # Encode to JPEG
                ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
                if not ret:
                    continue
                    
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                # Limit fps roughly
                time.sleep(0.05)  # ~20fps cap for stability
            except Exception as e:
                print(f"Stream error: {e}")
                time.sleep(0.1)

