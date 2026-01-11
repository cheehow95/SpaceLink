"""
Hardware Encoder Detection Module for SpaceLink
Detects and provides access to GPU hardware encoders (NVENC, QuickSync, AMF).
"""
import subprocess
import shutil
import platform
from typing import Optional, List, Dict
from dataclasses import dataclass
from enum import Enum


class EncoderType(Enum):
    SOFTWARE = "software"
    NVENC = "nvenc"
    QUICKSYNC = "quicksync"
    AMF = "amf"
    VIDEOTOOLBOX = "videotoolbox"


@dataclass
class EncoderInfo:
    """Information about an available encoder."""
    encoder_type: EncoderType
    name: str
    codec: str
    available: bool
    description: str


class HardwareEncoderManager:
    """Manages hardware encoder detection and selection."""
    
    def __init__(self):
        self._available_encoders: List[EncoderInfo] = []
        self._selected_encoder: Optional[EncoderInfo] = None
        self._ffmpeg_path: Optional[str] = None
        
        # Detect available encoders
        self._detect_encoders()
    
    def _detect_encoders(self):
        """Detect available hardware encoders."""
        self._available_encoders = []
        
        # Always add software encoder
        self._available_encoders.append(EncoderInfo(
            encoder_type=EncoderType.SOFTWARE,
            name="libx264",
            codec="h264",
            available=True,
            description="Software H.264 encoder (CPU)"
        ))
        
        # Check for ffmpeg
        self._ffmpeg_path = shutil.which("ffmpeg")
        if not self._ffmpeg_path:
            print("[HWEncoder] FFmpeg not found in PATH")
            self._selected_encoder = self._available_encoders[0]
            return
        
        # Query ffmpeg for available encoders
        try:
            result = subprocess.run(
                [self._ffmpeg_path, "-hide_banner", "-encoders"],
                capture_output=True,
                text=True,
                timeout=10
            )
            encoder_output = result.stdout.lower()
            
            # Check for NVIDIA NVENC
            if "h264_nvenc" in encoder_output:
                self._available_encoders.append(EncoderInfo(
                    encoder_type=EncoderType.NVENC,
                    name="h264_nvenc",
                    codec="h264",
                    available=self._test_encoder("h264_nvenc"),
                    description="NVIDIA NVENC H.264 encoder"
                ))
            
            if "hevc_nvenc" in encoder_output:
                self._available_encoders.append(EncoderInfo(
                    encoder_type=EncoderType.NVENC,
                    name="hevc_nvenc",
                    codec="hevc",
                    available=self._test_encoder("hevc_nvenc"),
                    description="NVIDIA NVENC HEVC encoder"
                ))
            
            # Check for Intel QuickSync
            if "h264_qsv" in encoder_output:
                self._available_encoders.append(EncoderInfo(
                    encoder_type=EncoderType.QUICKSYNC,
                    name="h264_qsv",
                    codec="h264",
                    available=self._test_encoder("h264_qsv"),
                    description="Intel QuickSync H.264 encoder"
                ))
            
            # Check for AMD AMF
            if "h264_amf" in encoder_output:
                self._available_encoders.append(EncoderInfo(
                    encoder_type=EncoderType.AMF,
                    name="h264_amf",
                    codec="h264",
                    available=self._test_encoder("h264_amf"),
                    description="AMD AMF H.264 encoder"
                ))
            
            # Check for Apple VideoToolbox (macOS)
            if "h264_videotoolbox" in encoder_output:
                self._available_encoders.append(EncoderInfo(
                    encoder_type=EncoderType.VIDEOTOOLBOX,
                    name="h264_videotoolbox",
                    codec="h264",
                    available=self._test_encoder("h264_videotoolbox"),
                    description="Apple VideoToolbox H.264 encoder"
                ))
                
        except Exception as e:
            print(f"[HWEncoder] Error detecting encoders: {e}")
        
        # Select best available encoder
        self._select_best_encoder()
        
        print(f"[HWEncoder] Available encoders: {[e.name for e in self._available_encoders if e.available]}")
        print(f"[HWEncoder] Selected: {self._selected_encoder.name if self._selected_encoder else 'None'}")
    
    def _test_encoder(self, encoder_name: str) -> bool:
        """Test if an encoder actually works."""
        if not self._ffmpeg_path:
            return False
        
        try:
            # Try to initialize the encoder with a tiny test
            result = subprocess.run(
                [
                    self._ffmpeg_path, "-hide_banner", "-y",
                    "-f", "lavfi", "-i", "color=c=black:s=16x16:d=0.1",
                    "-c:v", encoder_name,
                    "-f", "null", "-"
                ],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _select_best_encoder(self):
        """Select the best available encoder."""
        # Priority: NVENC > QuickSync > AMF > VideoToolbox > Software
        priority = [
            EncoderType.NVENC,
            EncoderType.QUICKSYNC,
            EncoderType.AMF,
            EncoderType.VIDEOTOOLBOX,
            EncoderType.SOFTWARE
        ]
        
        for encoder_type in priority:
            for encoder in self._available_encoders:
                if encoder.encoder_type == encoder_type and encoder.available:
                    self._selected_encoder = encoder
                    return
        
        # Fallback to software
        for encoder in self._available_encoders:
            if encoder.encoder_type == EncoderType.SOFTWARE:
                self._selected_encoder = encoder
                return
    
    def get_available_encoders(self) -> List[Dict]:
        """Get list of available encoders."""
        return [
            {
                "type": e.encoder_type.value,
                "name": e.name,
                "codec": e.codec,
                "available": e.available,
                "description": e.description,
                "selected": e == self._selected_encoder
            }
            for e in self._available_encoders
        ]
    
    def get_selected_encoder(self) -> Optional[Dict]:
        """Get currently selected encoder."""
        if self._selected_encoder:
            return {
                "type": self._selected_encoder.encoder_type.value,
                "name": self._selected_encoder.name,
                "codec": self._selected_encoder.codec,
                "description": self._selected_encoder.description
            }
        return None
    
    def select_encoder(self, encoder_name: str) -> Dict:
        """Select a specific encoder by name."""
        for encoder in self._available_encoders:
            if encoder.name == encoder_name and encoder.available:
                self._selected_encoder = encoder
                return {
                    "status": "ok",
                    "encoder": encoder.name,
                    "message": f"Selected encoder: {encoder.description}"
                }
        
        return {"status": "error", "message": f"Encoder not available: {encoder_name}"}
    
    def get_ffmpeg_encoder_args(self, quality: str = "medium") -> List[str]:
        """Get FFmpeg arguments for the selected encoder."""
        if not self._selected_encoder:
            return ["-c:v", "libx264", "-preset", "ultrafast"]
        
        encoder_name = self._selected_encoder.name
        
        # Quality presets
        quality_map = {
            "low": {"bitrate": "1000k", "preset": "ultrafast"},
            "medium": {"bitrate": "3000k", "preset": "fast"},
            "high": {"bitrate": "6000k", "preset": "medium"},
            "ultra": {"bitrate": "10000k", "preset": "slow"}
        }
        
        settings = quality_map.get(quality, quality_map["medium"])
        
        if self._selected_encoder.encoder_type == EncoderType.SOFTWARE:
            return [
                "-c:v", "libx264",
                "-preset", settings["preset"],
                "-tune", "zerolatency",
                "-b:v", settings["bitrate"]
            ]
        
        elif self._selected_encoder.encoder_type == EncoderType.NVENC:
            return [
                "-c:v", encoder_name,
                "-preset", "p4",  # NVENC preset
                "-tune", "ll",   # Low latency
                "-b:v", settings["bitrate"],
                "-rc", "cbr"
            ]
        
        elif self._selected_encoder.encoder_type == EncoderType.QUICKSYNC:
            return [
                "-c:v", encoder_name,
                "-preset", "faster",
                "-b:v", settings["bitrate"]
            ]
        
        elif self._selected_encoder.encoder_type == EncoderType.AMF:
            return [
                "-c:v", encoder_name,
                "-quality", "speed",
                "-b:v", settings["bitrate"]
            ]
        
        elif self._selected_encoder.encoder_type == EncoderType.VIDEOTOOLBOX:
            return [
                "-c:v", encoder_name,
                "-b:v", settings["bitrate"]
            ]
        
        return ["-c:v", "libx264", "-preset", "ultrafast"]
    
    def get_gpu_info(self) -> Dict:
        """Get information about available GPUs."""
        gpu_info = {"gpus": []}
        
        # Try to detect NVIDIA GPU
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    parts = line.split(',')
                    if len(parts) >= 2:
                        gpu_info["gpus"].append({
                            "vendor": "NVIDIA",
                            "name": parts[0].strip(),
                            "memory": parts[1].strip()
                        })
        except Exception:
            pass
        
        # Could add Intel/AMD detection here
        
        return gpu_info


# Global instance
hw_encoder_manager = HardwareEncoderManager()
