"""
Audio Capture Module for SpaceLink
Captures system audio (loopback) and provides it as a WebRTC audio track.
"""
import asyncio
import numpy as np
from av import AudioFrame
from aiortc import MediaStreamTrack
import threading
import queue

# Try to import audio libraries
try:
    import sounddevice as sd
    AUDIO_BACKEND = "sounddevice"
except ImportError:
    try:
        import pyaudio
        AUDIO_BACKEND = "pyaudio"
    except ImportError:
        AUDIO_BACKEND = None
        print("[Audio] Warning: No audio backend available. Install sounddevice or pyaudio.")


class AudioCaptureTrack(MediaStreamTrack):
    """
    A WebRTC audio track that captures system audio.
    """
    kind = "audio"
    
    def __init__(self, sample_rate: int = 48000, channels: int = 2):
        super().__init__()
        self.sample_rate = sample_rate
        self.channels = channels
        self._timestamp = 0
        self._samples_per_frame = 960  # 20ms at 48kHz
        self._audio_queue = queue.Queue(maxsize=50)
        self._running = False
        self._muted = False
        self._volume = 1.0
        self._capture_thread = None
        
        # Start capture
        self._start_capture()
    
    def _start_capture(self):
        """Start the audio capture thread."""
        if AUDIO_BACKEND is None:
            print("[Audio] No audio backend available, using silence")
            return
            
        self._running = True
        self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._capture_thread.start()
    
    def _capture_loop(self):
        """Capture audio in a background thread."""
        if AUDIO_BACKEND == "sounddevice":
            self._capture_sounddevice()
        elif AUDIO_BACKEND == "pyaudio":
            self._capture_pyaudio()
    
    def _capture_sounddevice(self):
        """Capture using sounddevice (WASAPI loopback on Windows)."""
        try:
            # Try to find a loopback device
            devices = sd.query_devices()
            loopback_device = None
            
            for i, dev in enumerate(devices):
                name = dev['name'].lower()
                # Windows WASAPI loopback devices often have these keywords
                if 'loopback' in name or 'stereo mix' in name or 'what u hear' in name:
                    loopback_device = i
                    break
            
            # If no loopback found, try default output as input (may require virtual audio cable)
            if loopback_device is None:
                default_output = sd.query_devices(kind='output')
                print(f"[Audio] No loopback device found. Using default output: {default_output['name']}")
                # Use default input as fallback
                loopback_device = None
            
            def audio_callback(indata, frames, time_info, status):
                if status:
                    print(f"[Audio] Status: {status}")
                if not self._audio_queue.full():
                    self._audio_queue.put(indata.copy())
            
            with sd.InputStream(
                device=loopback_device,
                samplerate=self.sample_rate,
                channels=self.channels,
                blocksize=self._samples_per_frame,
                callback=audio_callback
            ):
                while self._running:
                    sd.sleep(100)
                    
        except Exception as e:
            print(f"[Audio] sounddevice capture error: {e}")
            self._running = False
    
    def _capture_pyaudio(self):
        """Capture using PyAudio."""
        try:
            p = pyaudio.PyAudio()
            
            # Find loopback device
            loopback_index = None
            for i in range(p.get_device_count()):
                dev_info = p.get_device_info_by_index(i)
                name = dev_info['name'].lower()
                if 'loopback' in name or 'stereo mix' in name:
                    loopback_index = i
                    break
            
            stream = p.open(
                format=pyaudio.paFloat32,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=loopback_index,
                frames_per_buffer=self._samples_per_frame
            )
            
            while self._running:
                try:
                    data = stream.read(self._samples_per_frame, exception_on_overflow=False)
                    audio_data = np.frombuffer(data, dtype=np.float32).reshape(-1, self.channels)
                    if not self._audio_queue.full():
                        self._audio_queue.put(audio_data)
                except Exception as e:
                    print(f"[Audio] Read error: {e}")
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            
        except Exception as e:
            print(f"[Audio] PyAudio capture error: {e}")
            self._running = False
    
    def set_muted(self, muted: bool):
        """Mute/unmute the audio."""
        self._muted = muted
    
    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)."""
        self._volume = max(0.0, min(1.0, volume))
    
    async def recv(self):
        """Receive the next audio frame."""
        # Try to get captured audio
        try:
            audio_data = self._audio_queue.get_nowait()
        except queue.Empty:
            # Generate silence if no audio available
            audio_data = np.zeros((self._samples_per_frame, self.channels), dtype=np.float32)
        
        # Apply mute and volume
        if self._muted:
            audio_data = np.zeros_like(audio_data)
        else:
            audio_data = audio_data * self._volume
        
        # Convert to int16 for the audio frame
        audio_data = (audio_data * 32767).astype(np.int16)
        
        # Create audio frame
        frame = AudioFrame(format='s16', layout='stereo' if self.channels == 2 else 'mono', samples=self._samples_per_frame)
        frame.sample_rate = self.sample_rate
        frame.pts = self._timestamp
        self._timestamp += self._samples_per_frame
        
        # Fill frame with audio data
        frame.planes[0].update(audio_data.tobytes())
        
        # Control timing
        await asyncio.sleep(self._samples_per_frame / self.sample_rate)
        
        return frame
    
    def stop(self):
        """Stop audio capture."""
        self._running = False
        if self._capture_thread:
            self._capture_thread.join(timeout=1.0)


class AudioManager:
    """Manages audio capture settings."""
    
    def __init__(self):
        self.muted = False
        self.volume = 1.0
        self.active_tracks = []
    
    def create_track(self) -> AudioCaptureTrack:
        """Create a new audio capture track."""
        track = AudioCaptureTrack()
        track.set_muted(self.muted)
        track.set_volume(self.volume)
        self.active_tracks.append(track)
        return track
    
    def set_muted(self, muted: bool):
        """Set mute state for all tracks."""
        self.muted = muted
        for track in self.active_tracks:
            track.set_muted(muted)
    
    def set_volume(self, volume: float):
        """Set volume for all tracks."""
        self.volume = volume
        for track in self.active_tracks:
            track.set_volume(volume)
    
    def get_available_devices(self) -> list:
        """List available audio devices."""
        devices = []
        if AUDIO_BACKEND == "sounddevice":
            try:
                for i, dev in enumerate(sd.query_devices()):
                    if dev['max_input_channels'] > 0:
                        devices.append({
                            "index": i,
                            "name": dev['name'],
                            "channels": dev['max_input_channels'],
                            "sample_rate": dev['default_samplerate']
                        })
            except Exception as e:
                print(f"[Audio] Error listing devices: {e}")
        return devices


# Global instance
audio_manager = AudioManager()
