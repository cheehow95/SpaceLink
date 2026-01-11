"""
Advanced Codec Manager for SpaceLink v4.0
Intelligent codec selection and optimization.
"""
import subprocess
import platform
from typing import Optional, Dict, List


class CodecManager:
    """Manages video codec selection and optimization."""
    
    # Codec priority (higher = better quality/efficiency)
    CODEC_PRIORITY = {
        "av1": {"priority": 100, "quality": 10, "cpu_cost": 8, "hw_support": ["nvidia_av1", "intel_av1"]},
        "h265": {"priority": 90, "quality": 8, "cpu_cost": 3, "hw_support": ["nvenc_hevc", "amf_hevc", "qsv_hevc"]},
        "vp9": {"priority": 70, "quality": 7, "cpu_cost": 6, "hw_support": ["nvenc_vp9"]},
        "h264": {"priority": 60, "quality": 6, "cpu_cost": 2, "hw_support": ["nvenc", "amf", "qsv"]},
        "vp8": {"priority": 40, "quality": 5, "cpu_cost": 4, "hw_support": []},
    }
    
    def __init__(self):
        self.available_codecs = []
        self.hw_encoders = []
        self.current_codec = "h264"
        self.detect_capabilities()
    
    def detect_capabilities(self):
        """Detect available codecs and hardware encoders."""
        # Check FFmpeg codecs
        try:
            result = subprocess.run(
                ["ffmpeg", "-encoders"],
                capture_output=True, text=True, timeout=5
            )
            output = result.stdout.lower()
            
            # Check each codec
            if "hevc" in output or "libx265" in output:
                self.available_codecs.append("h265")
            if "h264" in output or "libx264" in output:
                self.available_codecs.append("h264")
            if "vp9" in output or "libvpx-vp9" in output:
                self.available_codecs.append("vp9")
            if "vp8" in output or "libvpx" in output:
                self.available_codecs.append("vp8")
            if "av1" in output or "libaom" in output or "libsvtav1" in output:
                self.available_codecs.append("av1")
            
            # Check hardware encoders
            if "nvenc" in output:
                self.hw_encoders.append("nvenc")
            if "h264_nvenc" in output:
                self.hw_encoders.append("nvenc_h264")
            if "hevc_nvenc" in output:
                self.hw_encoders.append("nvenc_hevc")
            if "h264_amf" in output:
                self.hw_encoders.append("amf")
            if "h264_qsv" in output:
                self.hw_encoders.append("qsv")
                
        except Exception as e:
            print(f"[CodecManager] FFmpeg detection failed: {e}")
            self.available_codecs = ["h264", "vp8"]
    
    def select_best_codec(self, 
                          prefer_hw: bool = True,
                          max_cpu_cost: int = 5,
                          min_quality: int = 5) -> Dict:
        """Select the best codec based on constraints."""
        candidates = []
        
        for codec, props in self.CODEC_PRIORITY.items():
            if codec not in self.available_codecs:
                continue
            if props["cpu_cost"] > max_cpu_cost and not prefer_hw:
                continue
            if props["quality"] < min_quality:
                continue
            
            # Check if hardware acceleration available
            has_hw = any(hw in self.hw_encoders for hw in props["hw_support"])
            
            score = props["priority"]
            if prefer_hw and has_hw:
                score += 20  # Boost for HW acceleration
            
            candidates.append({
                "codec": codec,
                "score": score,
                "hw_available": has_hw,
                **props
            })
        
        if not candidates:
            return {"codec": "h264", "hw_available": False, "quality": 6}
        
        # Sort by score
        candidates.sort(key=lambda x: x["score"], reverse=True)
        best = candidates[0]
        self.current_codec = best["codec"]
        
        return best
    
    def get_encoder_settings(self, codec: str, quality: str = "balanced") -> Dict:
        """Get optimized encoder settings for a codec."""
        presets = {
            "h264": {
                "fast": {"preset": "veryfast", "crf": 28, "bitrate": "2M"},
                "balanced": {"preset": "medium", "crf": 23, "bitrate": "4M"},
                "quality": {"preset": "slow", "crf": 18, "bitrate": "8M"}
            },
            "h265": {
                "fast": {"preset": "veryfast", "crf": 32, "bitrate": "1.5M"},
                "balanced": {"preset": "medium", "crf": 26, "bitrate": "3M"},
                "quality": {"preset": "slow", "crf": 20, "bitrate": "6M"}
            },
            "vp9": {
                "fast": {"speed": 8, "crf": 35, "bitrate": "2M"},
                "balanced": {"speed": 4, "crf": 30, "bitrate": "3.5M"},
                "quality": {"speed": 1, "crf": 24, "bitrate": "7M"}
            },
            "av1": {
                "fast": {"preset": 8, "crf": 40, "bitrate": "1M"},
                "balanced": {"preset": 5, "crf": 32, "bitrate": "2M"},
                "quality": {"preset": 3, "crf": 24, "bitrate": "4M"}
            }
        }
        
        return presets.get(codec, presets["h264"]).get(quality, presets["h264"]["balanced"])
    
    def get_status(self) -> Dict:
        """Get current codec manager status."""
        return {
            "available_codecs": self.available_codecs,
            "hw_encoders": self.hw_encoders,
            "current_codec": self.current_codec,
            "recommended": self.select_best_codec()
        }


# Global codec manager
codec_manager = CodecManager()


def get_best_codec() -> Dict:
    """Get the best available codec."""
    return codec_manager.select_best_codec()


def get_codec_status() -> Dict:
    """Get codec manager status."""
    return codec_manager.get_status()
