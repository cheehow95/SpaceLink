"""
VoIP Module for SpaceLink v4.1
Voice over IP for audio communication.
"""
import sys
import threading
from typing import Optional, Dict

# Audio availability check
try:
    import sounddevice as sd
    import numpy as np
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False


class VoIPManager:
    """Voice over IP manager for audio communication."""
    
    def __init__(self):
        self.is_transmitting = False
        self.is_receiving = False
        self.audio_stream = None
        self.sample_rate = 16000
        self.channels = 1
        self.muted = False
        self.volume = 1.0
        self.audio_buffer = []
    
    def get_audio_devices(self) -> Dict:
        """Get available audio input/output devices."""
        if not AUDIO_AVAILABLE:
            return {"inputs": [], "outputs": [], "available": False}
        
        try:
            devices = sd.query_devices()
            inputs = []
            outputs = []
            
            for i, d in enumerate(devices):
                info = {"id": i, "name": d["name"], "channels": d["max_input_channels"]}
                if d["max_input_channels"] > 0:
                    inputs.append(info)
                if d["max_output_channels"] > 0:
                    outputs.append(info)
            
            return {
                "inputs": inputs,
                "outputs": outputs,
                "available": True,
                "default_input": sd.default.device[0],
                "default_output": sd.default.device[1]
            }
        except Exception as e:
            return {"inputs": [], "outputs": [], "available": False, "error": str(e)}
    
    def start_capture(self, device_id: Optional[int] = None) -> Dict:
        """Start capturing audio from microphone."""
        if not AUDIO_AVAILABLE:
            return {"status": "error", "message": "Audio not available"}
        
        if self.is_transmitting:
            return {"status": "error", "message": "Already capturing"}
        
        try:
            def audio_callback(indata, frames, time, status):
                if not self.muted:
                    # Store audio data for transmission
                    self.audio_buffer.extend(indata.flatten().tolist())
                    # Keep buffer at reasonable size
                    if len(self.audio_buffer) > self.sample_rate * 2:
                        self.audio_buffer = self.audio_buffer[-self.sample_rate:]
            
            self.audio_stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                device=device_id,
                callback=audio_callback
            )
            self.audio_stream.start()
            self.is_transmitting = True
            
            return {"status": "ok", "message": "Audio capture started"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def stop_capture(self) -> Dict:
        """Stop audio capture."""
        if self.audio_stream:
            self.audio_stream.stop()
            self.audio_stream.close()
            self.audio_stream = None
        
        self.is_transmitting = False
        self.audio_buffer.clear()
        return {"status": "ok", "message": "Audio capture stopped"}
    
    def get_audio_data(self) -> Dict:
        """Get captured audio data."""
        if not self.audio_buffer:
            return {"data": [], "length": 0}
        
        data = self.audio_buffer.copy()
        self.audio_buffer.clear()
        return {"data": data, "length": len(data)}
    
    def play_audio(self, audio_data: list, device_id: Optional[int] = None) -> Dict:
        """Play received audio."""
        if not AUDIO_AVAILABLE:
            return {"status": "error", "message": "Audio not available"}
        
        try:
            audio = np.array(audio_data, dtype=np.float32) * self.volume
            sd.play(audio, samplerate=self.sample_rate, device=device_id)
            return {"status": "ok", "message": "Playing audio"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def set_mute(self, muted: bool) -> Dict:
        """Mute/unmute microphone."""
        self.muted = muted
        return {"status": "ok", "muted": muted}
    
    def set_volume(self, volume: float) -> Dict:
        """Set playback volume (0.0 - 1.0)."""
        self.volume = max(0.0, min(1.0, volume))
        return {"status": "ok", "volume": self.volume}
    
    def get_status(self) -> Dict:
        """Get VoIP status."""
        return {
            "available": AUDIO_AVAILABLE,
            "transmitting": self.is_transmitting,
            "muted": self.muted,
            "volume": self.volume,
            "sample_rate": self.sample_rate
        }


# Global VoIP manager
voip_manager = VoIPManager()


def get_voip_status() -> Dict:
    """Get VoIP status."""
    return voip_manager.get_status()


def get_audio_devices() -> Dict:
    """Get audio devices."""
    return voip_manager.get_audio_devices()


def start_voice_capture(device_id: int = None) -> Dict:
    """Start voice capture."""
    return voip_manager.start_capture(device_id)


def stop_voice_capture() -> Dict:
    """Stop voice capture."""
    return voip_manager.stop_capture()
