"""
WebRTC Server Module for SpaceLink
Uses aiortc to create WebRTC connections with video streaming, audio streaming, and data channels.
"""
import asyncio
import json
import fractions
from av import VideoFrame
import numpy as np

from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack, RTCConfiguration, RTCIceServer
from aiortc.contrib.media import MediaBlackhole

from modules.stream_capture import ScreenCapture
from core.input_control import execute_command

# Try to import audio capture
try:
    from modules.audio_capture import audio_manager, AudioCaptureTrack
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("[WebRTC] Audio capture module not available")

# Google's free STUN servers
ICE_SERVERS = [
    RTCIceServer(urls=["stun:stun.l.google.com:19302"]),
    RTCIceServer(urls=["stun:stun1.l.google.com:19302"]),
    RTCIceServer(urls=["stun:stun2.l.google.com:19302"]),
]

class ScreenVideoTrack(VideoStreamTrack):
    """
    A video track that captures the screen and sends frames via WebRTC.
    """
    kind = "video"
    
    def __init__(self, screen_capture: ScreenCapture, fps: int = 15, max_width: int = 1280):
        super().__init__()
        self.screen_capture = screen_capture
        self.fps = fps
        self.max_width = max_width
        self._timestamp = 0
        self._start_time = None
    
    def update_settings(self, fps: int = None, max_width: int = None):
        if fps:
            self.fps = fps
        if max_width:
            self.max_width = max_width
        
    async def recv(self):
        # Calculate timing
        pts, time_base = await self.next_timestamp()
        
        # Capture screen (run in executor to not block event loop)
        loop = asyncio.get_event_loop()
        frame_bgr = await loop.run_in_executor(None, self.screen_capture.get_frame)
        
        # Resize for bandwidth efficiency
        import cv2
        height, width = frame_bgr.shape[:2]
        new_width = min(self.max_width, width)
        new_height = int(height * (new_width / width))
        frame_bgr = cv2.resize(frame_bgr, (new_width, new_height))
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        
        # Create VideoFrame
        video_frame = VideoFrame.from_ndarray(frame_rgb, format="rgb24")
        video_frame.pts = pts
        video_frame.time_base = time_base
        
        # Control frame rate
        await asyncio.sleep(1 / self.fps)
        
        return video_frame


class WebRTCManager:
    """
    Manages WebRTC peer connections for SpaceLink.
    """
    def __init__(self):
        self.screen_capture = ScreenCapture()
        self.peer_connections = set()
        self.data_channels = []
        self.fps = 15
        self.max_width = 1280
        self.audio_enabled = AUDIO_AVAILABLE
        
    def update_settings(self, fps: int = None, max_width: int = None, audio_enabled: bool = None):
        """Update video and audio settings."""
        if fps is not None:
            self.fps = fps
        if max_width is not None:
            self.max_width = max_width
        if audio_enabled is not None and AUDIO_AVAILABLE:
            self.audio_enabled = audio_enabled
        print(f"[WebRTC] Settings updated: fps={self.fps}, max_width={self.max_width}, audio={self.audio_enabled}")
        
        # Update all active video tracks
        for pc in self.peer_connections:
            for transceiver in pc.getTransceivers():
                if transceiver.sender.track and isinstance(transceiver.sender.track, ScreenVideoTrack):
                    transceiver.sender.track.update_settings(fps=self.fps, max_width=self.max_width)
        
    def get_rtc_configuration(self):
        return RTCConfiguration(iceServers=ICE_SERVERS)
    
    async def create_offer(self):
        """
        Creates a new peer connection and generates an offer.
        Returns the offer SDP and the peer connection.
        """
        pc = RTCPeerConnection(configuration=self.get_rtc_configuration())
        self.peer_connections.add(pc)
        
        # Add video track with current settings
        video_track = ScreenVideoTrack(self.screen_capture, fps=self.fps, max_width=self.max_width)
        pc.addTrack(video_track)
        
        # Add audio track if available and enabled
        if AUDIO_AVAILABLE and self.audio_enabled:
            try:
                audio_track = audio_manager.create_track()
                pc.addTrack(audio_track)
                print("[WebRTC] Audio track added")
            except Exception as e:
                print(f"[WebRTC] Could not add audio track: {e}")
        
        # Create data channel for control commands
        channel = pc.createDataChannel("control", ordered=True)
        self.data_channels.append(channel)
        
        @channel.on("message")
        def on_message(message):
            try:
                command = json.loads(message)
                if command.get("type") == "config":
                    data = command.get("data", {})
                    self.update_settings(fps=data.get("fps"), max_width=data.get("max_width"))
                else:
                    print(f"[WebRTC] Received command: {command}")
                    execute_command(command)
            except Exception as e:
                print(f"[WebRTC] Error processing command: {e}")
        
        @channel.on("open")
        def on_open():
            print("[WebRTC] Data channel opened")
            
        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            print(f"[WebRTC] Connection state: {pc.connectionState}")
            if pc.connectionState == "failed" or pc.connectionState == "closed":
                await self.cleanup_peer_connection(pc)
        
        # Create offer
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        
        # Wait for ICE gathering to complete
        await self._wait_for_ice_gathering(pc)
        
        return {
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type
        }, pc
    
    async def handle_answer(self, pc: RTCPeerConnection, answer_sdp: dict):
        """
        Handles the answer from the remote peer.
        """
        answer = RTCSessionDescription(sdp=answer_sdp["sdp"], type=answer_sdp["type"])
        await pc.setRemoteDescription(answer)
        print("[WebRTC] Answer set, connection establishing...")
        
    async def handle_offer(self, offer_sdp: dict):
        """
        Handles an offer from a remote peer (when PC acts as answerer).
        """
        pc = RTCPeerConnection(configuration=self.get_rtc_configuration())
        self.peer_connections.add(pc)
        
        # Add video track with current settings
        video_track = ScreenVideoTrack(self.screen_capture, fps=self.fps, max_width=self.max_width)
        pc.addTrack(video_track)
        
        # Add audio track if available and enabled
        if AUDIO_AVAILABLE and self.audio_enabled:
            try:
                audio_track = audio_manager.create_track()
                pc.addTrack(audio_track)
                print("[WebRTC] Audio track added")
            except Exception as e:
                print(f"[WebRTC] Could not add audio track: {e}")
        
        @pc.on("datachannel")
        def on_datachannel(channel):
            print(f"[WebRTC] Data channel received: {channel.label}")
            self.data_channels.append(channel)
            
            @channel.on("message")
            def on_message(message):
                try:
                    command = json.loads(message)
                    print(f"[WebRTC] Received command: {command}")
                    execute_command(command)
                except Exception as e:
                    print(f"[WebRTC] Error processing command: {e}")
        
        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            print(f"[WebRTC] Connection state: {pc.connectionState}")
            if pc.connectionState == "failed" or pc.connectionState == "closed":
                await self.cleanup_peer_connection(pc)
        
        # Set remote description (the offer)
        offer = RTCSessionDescription(sdp=offer_sdp["sdp"], type=offer_sdp["type"])
        await pc.setRemoteDescription(offer)
        
        # Create answer
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        
        # Wait for ICE gathering
        await self._wait_for_ice_gathering(pc)
        
        return {
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type
        }, pc
    
    async def _wait_for_ice_gathering(self, pc: RTCPeerConnection, timeout: float = 5.0):
        """Wait for ICE gathering to complete."""
        if pc.iceGatheringState == "complete":
            return
            
        gathering_complete = asyncio.Event()
        
        @pc.on("icegatheringstatechange")
        def on_ice_gathering_state_change():
            if pc.iceGatheringState == "complete":
                gathering_complete.set()
        
        try:
            await asyncio.wait_for(gathering_complete.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            print("[WebRTC] ICE gathering timed out, proceeding with available candidates")
    
    async def cleanup_peer_connection(self, pc: RTCPeerConnection):
        """Clean up a peer connection."""
        if pc in self.peer_connections:
            self.peer_connections.discard(pc)
            await pc.close()
            print("[WebRTC] Peer connection closed and cleaned up")
    
    async def cleanup_all(self):
        """Clean up all peer connections."""
        for pc in list(self.peer_connections):
            await pc.close()
        self.peer_connections.clear()
        self.data_channels.clear()


# Global instance
webrtc_manager = WebRTCManager()
