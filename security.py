"""
Security Module for SpaceLink v4.0
AES-256 encryption and 2FA support.
"""
import os
import hashlib
import hmac
import base64
import time
import secrets
from typing import Optional, Tuple

# Try to import cryptography for AES
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("[Security] cryptography not installed, AES disabled")

# Try to import pyotp for 2FA
try:
    import pyotp
    TOTP_AVAILABLE = True
except ImportError:
    TOTP_AVAILABLE = False
    print("[Security] pyotp not installed, 2FA disabled")


class AESEncryption:
    """AES-256 encryption for secure communication."""
    
    def __init__(self, key: Optional[bytes] = None):
        if key is None:
            self.key = os.urandom(32)  # 256 bits
        else:
            self.key = key
        self.enabled = CRYPTO_AVAILABLE
    
    def encrypt(self, plaintext: bytes) -> Tuple[bytes, bytes]:
        """Encrypt data with AES-256-GCM."""
        if not self.enabled:
            return plaintext, b""
        
        iv = os.urandom(16)
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        
        return ciphertext, iv + encryptor.tag
    
    def decrypt(self, ciphertext: bytes, iv_tag: bytes) -> bytes:
        """Decrypt AES-256-GCM data."""
        if not self.enabled:
            return ciphertext
        
        iv = iv_tag[:16]
        tag = iv_tag[16:]
        
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.GCM(iv, tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()
    
    def encrypt_base64(self, plaintext: str) -> str:
        """Encrypt string and return base64."""
        ciphertext, iv_tag = self.encrypt(plaintext.encode())
        return base64.b64encode(iv_tag + ciphertext).decode()
    
    def decrypt_base64(self, encoded: str) -> str:
        """Decrypt base64 encoded data."""
        data = base64.b64decode(encoded)
        iv_tag = data[:32]
        ciphertext = data[32:]
        return self.decrypt(ciphertext, iv_tag).decode()
    
    def get_key_b64(self) -> str:
        """Get key as base64 for storage."""
        return base64.b64encode(self.key).decode()
    
    @classmethod
    def from_key_b64(cls, key_b64: str) -> "AESEncryption":
        """Create from base64 key."""
        key = base64.b64decode(key_b64)
        return cls(key)


class TwoFactorAuth:
    """TOTP-based two-factor authentication."""
    
    def __init__(self):
        self.enabled = TOTP_AVAILABLE
        self.secrets = {}  # user_id -> secret
    
    def generate_secret(self, user_id: str = "default") -> str:
        """Generate a new TOTP secret for a user."""
        if not self.enabled:
            return ""
        
        secret = pyotp.random_base32()
        self.secrets[user_id] = secret
        return secret
    
    def get_qr_uri(self, user_id: str = "default", issuer: str = "SpaceLink") -> str:
        """Get the provisioning URI for QR code."""
        if not self.enabled or user_id not in self.secrets:
            return ""
        
        totp = pyotp.TOTP(self.secrets[user_id])
        return totp.provisioning_uri(name=user_id, issuer_name=issuer)
    
    def verify(self, user_id: str, code: str) -> bool:
        """Verify a TOTP code."""
        if not self.enabled:
            return True  # Skip if not available
        
        if user_id not in self.secrets:
            return False
        
        totp = pyotp.TOTP(self.secrets[user_id])
        return totp.verify(code, valid_window=1)
    
    def get_current_code(self, user_id: str = "default") -> str:
        """Get current TOTP code (for testing)."""
        if not self.enabled or user_id not in self.secrets:
            return ""
        
        totp = pyotp.TOTP(self.secrets[user_id])
        return totp.now()


class SecurityManager:
    """Main security manager for SpaceLink."""
    
    def __init__(self):
        self.aes = AESEncryption()
        self.twofa = TwoFactorAuth()
        self.secure_sessions = {}
    
    def create_secure_session(self, user_id: str) -> dict:
        """Create a new secure session."""
        session_key = secrets.token_hex(32)
        session_aes = AESEncryption()
        
        self.secure_sessions[session_key] = {
            "user_id": user_id,
            "created": time.time(),
            "aes": session_aes,
            "verified_2fa": False
        }
        
        return {
            "session_key": session_key,
            "encryption_key": session_aes.get_key_b64()
        }
    
    def verify_2fa(self, session_key: str, code: str) -> bool:
        """Verify 2FA for a session."""
        if session_key not in self.secure_sessions:
            return False
        
        session = self.secure_sessions[session_key]
        user_id = session["user_id"]
        
        if self.twofa.verify(user_id, code):
            session["verified_2fa"] = True
            return True
        return False
    
    def encrypt_message(self, session_key: str, message: str) -> str:
        """Encrypt a message for a session."""
        if session_key not in self.secure_sessions:
            return message
        
        aes = self.secure_sessions[session_key]["aes"]
        return aes.encrypt_base64(message)
    
    def decrypt_message(self, session_key: str, encrypted: str) -> str:
        """Decrypt a message from a session."""
        if session_key not in self.secure_sessions:
            return encrypted
        
        aes = self.secure_sessions[session_key]["aes"]
        return aes.decrypt_base64(encrypted)
    
    def get_status(self) -> dict:
        return {
            "aes_available": CRYPTO_AVAILABLE,
            "totp_available": TOTP_AVAILABLE,
            "active_sessions": len(self.secure_sessions)
        }


# Global security manager
security_manager = SecurityManager()


def get_security_status() -> dict:
    """Get security module status."""
    return security_manager.get_status()


def setup_2fa(user_id: str = "default") -> dict:
    """Setup 2FA for a user."""
    secret = security_manager.twofa.generate_secret(user_id)
    uri = security_manager.twofa.get_qr_uri(user_id)
    return {
        "secret": secret,
        "qr_uri": uri
    }


def verify_2fa(user_id: str, code: str) -> bool:
    """Verify 2FA code."""
    return security_manager.twofa.verify(user_id, code)
