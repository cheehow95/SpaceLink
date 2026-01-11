"""
Network Optimizer for SpaceLink v4.0
Adaptive bitrate, jitter buffer, and QoS management.
"""
import time
import statistics
from collections import deque
from dataclasses import dataclass
from typing import Optional, Dict, List


@dataclass
class NetworkMetrics:
    """Network quality metrics."""
    latency: float = 0
    jitter: float = 0
    packet_loss: float = 0
    bandwidth: float = 0
    quality_score: int = 100  # 0-100


class JitterBuffer:
    """Adaptive jitter buffer for smooth playback."""
    
    def __init__(self, min_delay: int = 20, max_delay: int = 200, target_delay: int = 50):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.target_delay = target_delay
        self.current_delay = target_delay
        self.arrival_times = deque(maxlen=100)
        self.jitter_history = deque(maxlen=50)
    
    def add_packet(self, timestamp: float):
        """Record packet arrival."""
        now = time.time() * 1000
        self.arrival_times.append(now)
        
        if len(self.arrival_times) >= 2:
            inter_arrival = self.arrival_times[-1] - self.arrival_times[-2]
            self.jitter_history.append(inter_arrival)
    
    def calculate_optimal_delay(self) -> int:
        """Calculate optimal buffer delay based on jitter."""
        if len(self.jitter_history) < 5:
            return self.target_delay
        
        # Calculate jitter (standard deviation of inter-arrival times)
        jitter = statistics.stdev(self.jitter_history)
        
        # Optimal delay = mean + 2*jitter for 95% confidence
        mean_delay = statistics.mean(self.jitter_history)
        optimal = int(mean_delay + 2 * jitter)
        
        # Clamp to bounds
        self.current_delay = max(self.min_delay, min(self.max_delay, optimal))
        return self.current_delay
    
    def get_status(self) -> Dict:
        return {
            "current_delay": self.current_delay,
            "jitter": statistics.stdev(self.jitter_history) if len(self.jitter_history) > 1 else 0,
            "buffer_size": len(self.arrival_times)
        }


class AdaptiveBitrate:
    """Adaptive bitrate controller."""
    
    QUALITY_PRESETS = {
        "4k": {"width": 3840, "height": 2160, "bitrate": 15000, "fps": 60},
        "1440p": {"width": 2560, "height": 1440, "bitrate": 8000, "fps": 60},
        "1080p": {"width": 1920, "height": 1080, "bitrate": 5000, "fps": 60},
        "720p": {"width": 1280, "height": 720, "bitrate": 2500, "fps": 30},
        "480p": {"width": 854, "height": 480, "bitrate": 1000, "fps": 30},
        "360p": {"width": 640, "height": 360, "bitrate": 500, "fps": 24},
    }
    
    def __init__(self):
        self.current_preset = "1080p"
        self.latency_history = deque(maxlen=30)
        self.bandwidth_history = deque(maxlen=20)
        self.last_adjustment = time.time()
        self.adjustment_cooldown = 3  # seconds
    
    def update_metrics(self, latency: float, bandwidth: float):
        """Update network metrics."""
        self.latency_history.append(latency)
        self.bandwidth_history.append(bandwidth)
    
    def calculate_quality(self) -> str:
        """Calculate optimal quality based on metrics."""
        if len(self.latency_history) < 3:
            return self.current_preset
        
        # Check cooldown
        if time.time() - self.last_adjustment < self.adjustment_cooldown:
            return self.current_preset
        
        avg_latency = statistics.mean(self.latency_history)
        avg_bandwidth = statistics.mean(self.bandwidth_history) if self.bandwidth_history else 5000
        
        # Quality selection logic
        if avg_latency > 150 or avg_bandwidth < 1000:
            target = "480p"
        elif avg_latency > 100 or avg_bandwidth < 2000:
            target = "720p"
        elif avg_latency > 50 or avg_bandwidth < 5000:
            target = "1080p"
        elif avg_latency > 20 or avg_bandwidth < 10000:
            target = "1440p"
        else:
            target = "4k"
        
        if target != self.current_preset:
            self.last_adjustment = time.time()
            self.current_preset = target
        
        return self.current_preset
    
    def get_settings(self) -> Dict:
        """Get current quality settings."""
        preset = self.calculate_quality()
        return {
            "preset": preset,
            **self.QUALITY_PRESETS[preset]
        }


class NetworkOptimizer:
    """Main network optimization controller."""
    
    def __init__(self):
        self.jitter_buffer = JitterBuffer()
        self.adaptive_bitrate = AdaptiveBitrate()
        self.metrics = NetworkMetrics()
        self.measurement_history = deque(maxlen=100)
    
    def update(self, latency: float, packet_loss: float = 0, bandwidth: float = 5000):
        """Update network state."""
        self.metrics.latency = latency
        self.metrics.packet_loss = packet_loss
        self.metrics.bandwidth = bandwidth
        
        # Update components
        self.jitter_buffer.add_packet(time.time() * 1000)
        self.adaptive_bitrate.update_metrics(latency, bandwidth)
        
        # Calculate quality score (0-100)
        latency_score = max(0, 100 - latency)
        loss_score = max(0, 100 - packet_loss * 100)
        self.metrics.quality_score = int((latency_score + loss_score) / 2)
        
        self.measurement_history.append({
            "timestamp": time.time(),
            "latency": latency,
            "quality": self.metrics.quality_score
        })
    
    def get_recommended_settings(self) -> Dict:
        """Get recommended video settings."""
        quality = self.adaptive_bitrate.get_settings()
        buffer = self.jitter_buffer.calculate_optimal_delay()
        
        return {
            "video": quality,
            "buffer_delay": buffer,
            "quality_score": self.metrics.quality_score,
            "current_latency": self.metrics.latency
        }
    
    def get_status(self) -> Dict:
        return {
            "metrics": {
                "latency": self.metrics.latency,
                "jitter": self.metrics.jitter,
                "packet_loss": self.metrics.packet_loss,
                "quality_score": self.metrics.quality_score
            },
            "jitter_buffer": self.jitter_buffer.get_status(),
            "adaptive_bitrate": self.adaptive_bitrate.get_settings()
        }


# Global optimizer
network_optimizer = NetworkOptimizer()


def optimize_network(latency: float, packet_loss: float = 0, bandwidth: float = 5000) -> Dict:
    """Update and get optimization recommendations."""
    network_optimizer.update(latency, packet_loss, bandwidth)
    return network_optimizer.get_recommended_settings()


def get_network_status() -> Dict:
    """Get network optimizer status."""
    return network_optimizer.get_status()
