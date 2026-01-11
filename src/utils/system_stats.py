"""
System Stats Module for SpaceLink
Provides CPU, RAM, Disk, Network, and Process monitoring.
"""
import platform
import psutil
from typing import List, Dict


def get_cpu_usage() -> dict:
    """Get CPU usage percentage."""
    return {
        "percent": psutil.cpu_percent(interval=0.1),
        "cores": psutil.cpu_count(),
        "frequency": psutil.cpu_freq().current if psutil.cpu_freq() else 0
    }


def get_memory_usage() -> dict:
    """Get RAM usage."""
    mem = psutil.virtual_memory()
    return {
        "total_gb": round(mem.total / (1024**3), 2),
        "used_gb": round(mem.used / (1024**3), 2),
        "percent": mem.percent
    }


def get_disk_usage() -> dict:
    """Get disk usage for main drive."""
    try:
        if platform.system() == "Windows":
            disk = psutil.disk_usage("C:\\")
        else:
            disk = psutil.disk_usage("/")
        return {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "percent": disk.percent
        }
    except:
        return {"total_gb": 0, "used_gb": 0, "percent": 0}


def get_network_stats() -> dict:
    """Get network I/O stats."""
    net = psutil.net_io_counters()
    return {
        "bytes_sent": net.bytes_sent,
        "bytes_recv": net.bytes_recv,
        "mb_sent": round(net.bytes_sent / (1024**2), 2),
        "mb_recv": round(net.bytes_recv / (1024**2), 2)
    }


def get_top_processes(n: int = 5) -> List[Dict]:
    """Get top N processes by CPU usage."""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            info = proc.info
            processes.append({
                "pid": info['pid'],
                "name": info['name'][:20],
                "cpu": round(info['cpu_percent'] or 0, 1),
                "mem": round(info['memory_percent'] or 0, 1)
            })
        except:
            pass
    
    # Sort by CPU usage
    processes.sort(key=lambda x: x['cpu'], reverse=True)
    return processes[:n]


def get_all_stats() -> dict:
    """Get all system stats."""
    return {
        "cpu": get_cpu_usage(),
        "memory": get_memory_usage(),
        "disk": get_disk_usage(),
        "network": get_network_stats(),
        "top_processes": get_top_processes(5)
    }


def get_battery() -> dict:
    """Get battery status if available."""
    try:
        battery = psutil.sensors_battery()
        if battery:
            return {
                "percent": battery.percent,
                "plugged": battery.power_plugged,
                "time_left": battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else -1
            }
    except:
        pass
    return {"percent": 100, "plugged": True, "time_left": -1}
