"""
Wake-on-LAN Module for SpaceLink
Enables waking the PC remotely from sleep/hibernate.
"""
import socket
import struct
import re
import json
from pathlib import Path
from typing import Optional, Dict, List


# Config file for storing MAC addresses
CONFIG_FILE = Path.home() / ".spacelink_wol_config.json"


def create_magic_packet(mac_address: str) -> bytes:
    """
    Create a Wake-on-LAN magic packet.
    
    The magic packet consists of:
    - 6 bytes of 0xFF
    - 16 repetitions of the target MAC address (6 bytes each)
    - Total: 102 bytes
    """
    # Remove separators and validate MAC address
    mac = mac_address.replace(':', '').replace('-', '').replace('.', '').upper()
    
    if len(mac) != 12:
        raise ValueError(f"Invalid MAC address format: {mac_address}")
    
    if not all(c in '0123456789ABCDEF' for c in mac):
        raise ValueError(f"Invalid MAC address characters: {mac_address}")
    
    # Convert to bytes
    mac_bytes = bytes.fromhex(mac)
    
    # Create magic packet: 6 bytes of 0xFF + MAC repeated 16 times
    magic = b'\xff' * 6 + mac_bytes * 16
    
    return magic


def send_magic_packet(mac_address: str, broadcast_ip: str = "255.255.255.255", 
                      port: int = 9) -> Dict:
    """
    Send a Wake-on-LAN magic packet.
    
    Args:
        mac_address: Target device MAC address (e.g., "AA:BB:CC:DD:EE:FF")
        broadcast_ip: Broadcast IP address (default: 255.255.255.255)
        port: WoL port (default: 9, sometimes 7)
    
    Returns:
        Status dict with success/error information
    """
    try:
        # Create magic packet
        packet = create_magic_packet(mac_address)
        
        # Send via UDP broadcast
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        # Send to both common ports
        sock.sendto(packet, (broadcast_ip, 9))
        sock.sendto(packet, (broadcast_ip, 7))
        
        sock.close()
        
        return {
            "status": "ok",
            "message": f"Magic packet sent to {mac_address}",
            "broadcast_ip": broadcast_ip,
            "port": port
        }
        
    except ValueError as e:
        return {"status": "error", "message": str(e)}
    except socket.error as e:
        return {"status": "error", "message": f"Socket error: {e}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def validate_mac_address(mac_address: str) -> bool:
    """Validate a MAC address format."""
    # Common formats: AA:BB:CC:DD:EE:FF, AA-BB-CC-DD-EE-FF, AABBCCDDEEFF
    pattern = r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$|^[0-9A-Fa-f]{12}$'
    return bool(re.match(pattern, mac_address))


def get_local_mac_addresses() -> List[Dict]:
    """Get MAC addresses of local network interfaces."""
    macs = []
    
    try:
        import uuid
        import psutil
        
        # Get network interface info
        for iface, addrs in psutil.net_if_addrs().items():
            mac = None
            ips = []
            
            for addr in addrs:
                if addr.family == psutil.AF_LINK:  # MAC address
                    mac = addr.address
                elif addr.family == socket.AF_INET:  # IPv4
                    ips.append(addr.address)
            
            if mac and mac != '00:00:00:00:00:00':
                macs.append({
                    "interface": iface,
                    "mac": mac,
                    "ips": ips
                })
                
    except ImportError:
        # Fallback: get just the primary MAC
        try:
            import uuid
            mac = ':'.join(format(x, '02x') for x in uuid.getnode().to_bytes(6, 'big'))
            macs.append({
                "interface": "primary",
                "mac": mac,
                "ips": []
            })
        except:
            pass
    
    return macs


class WakeOnLANManager:
    """Manages Wake-on-LAN configuration and operations."""
    
    def __init__(self):
        self._saved_devices: Dict[str, Dict] = {}
        self._load_config()
        
        # Get local MAC for reference
        self._local_macs = get_local_mac_addresses()
        if self._local_macs:
            print(f"[WoL] Local MAC: {self._local_macs[0].get('mac', 'Unknown')}")
    
    def _load_config(self):
        """Load saved device configuration."""
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r') as f:
                    self._saved_devices = json.load(f)
                print(f"[WoL] Loaded {len(self._saved_devices)} saved devices")
        except Exception as e:
            print(f"[WoL] Error loading config: {e}")
            self._saved_devices = {}
    
    def _save_config(self):
        """Save device configuration."""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self._saved_devices, f, indent=2)
        except Exception as e:
            print(f"[WoL] Error saving config: {e}")
    
    def wake(self, mac_address: Optional[str] = None, device_name: Optional[str] = None,
             broadcast_ip: str = "255.255.255.255") -> Dict:
        """
        Wake a device by MAC address or saved device name.
        """
        # Get MAC from device name if provided
        if device_name and not mac_address:
            if device_name in self._saved_devices:
                mac_address = self._saved_devices[device_name].get("mac")
            else:
                return {"status": "error", "message": f"Device not found: {device_name}"}
        
        if not mac_address:
            return {"status": "error", "message": "MAC address required"}
        
        if not validate_mac_address(mac_address):
            return {"status": "error", "message": f"Invalid MAC format: {mac_address}"}
        
        return send_magic_packet(mac_address, broadcast_ip)
    
    def save_device(self, name: str, mac_address: str, 
                    description: str = "", broadcast_ip: str = "255.255.255.255") -> Dict:
        """Save a device for quick access."""
        if not validate_mac_address(mac_address):
            return {"status": "error", "message": f"Invalid MAC format: {mac_address}"}
        
        self._saved_devices[name] = {
            "mac": mac_address.upper().replace('-', ':'),
            "description": description,
            "broadcast_ip": broadcast_ip
        }
        
        self._save_config()
        
        return {
            "status": "ok",
            "message": f"Device saved: {name}",
            "device": self._saved_devices[name]
        }
    
    def remove_device(self, name: str) -> Dict:
        """Remove a saved device."""
        if name in self._saved_devices:
            del self._saved_devices[name]
            self._save_config()
            return {"status": "ok", "message": f"Device removed: {name}"}
        return {"status": "error", "message": f"Device not found: {name}"}
    
    def get_saved_devices(self) -> Dict:
        """Get list of saved devices."""
        return {
            "status": "ok",
            "devices": self._saved_devices
        }
    
    def get_local_info(self) -> Dict:
        """Get local network interface information."""
        return {
            "status": "ok",
            "interfaces": self._local_macs
        }
    
    def get_this_pc_mac(self) -> Optional[str]:
        """Get this PC's primary MAC address."""
        if self._local_macs:
            return self._local_macs[0].get("mac")
        return None


# Global instance
wol_manager = WakeOnLANManager()
