# 🛰️ SpaceLink

<p align="center">
  <img src="icon.png" alt="SpaceLink Logo" width="200"/>
</p>

<p align="center">
  <strong>Ultra-Low Latency Remote Desktop Solution</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-4.1-blue.svg" alt="Version"/>
  <img src="https://img.shields.io/badge/python-3.8+-green.svg" alt="Python"/>
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg" alt="Platform"/>
  <img src="https://img.shields.io/badge/license-MIT-orange.svg" alt="License"/>
</p>

---

## ✨ Features

SpaceLink is a feature-rich remote desktop solution inspired by industry leaders like **Parsec**, **AnyDesk**, and **TeamViewer**.

### 🎮 Core Features
| Feature | Description |
|---------|-------------|
| 📺 **WebRTC Streaming** | Ultra-low latency video streaming |
| 🎮 **Gamepad Support** | Full controller support with analog sticks |
| 👆 **Touch Gestures** | Pinch-to-zoom, swipe, double-tap |
| 🔊 **Audio Streaming** | Real-time audio capture |
| 📁 **File Transfer** | Drag & drop file sharing |
| 📋 **Clipboard Sync** | Cross-device clipboard |

### ⚡ Performance
| Feature | Description |
|---------|-------------|
| 🎥 **Adaptive Bitrate** | 360p to 4K@60Hz |
| 🔧 **Hardware Encoding** | NVENC, AMF, QuickSync |
| 📊 **Codec Selection** | AV1, H.265, VP9, H.264 |
| 📈 **Jitter Buffer** | Adaptive network optimization |

### 🔒 Security
| Feature | Description |
|---------|-------------|
| 🔐 **AES-256 Encryption** | Military-grade security |
| 📱 **2FA Authentication** | TOTP Google Authenticator |
| 📝 **Audit Logging** | Complete session history |
| 🔑 **Token Sessions** | Secure session management |

### 🤝 Collaboration
| Feature | Description |
|---------|-------------|
| 👥 **Multi-User Sessions** | Up to 10 concurrent users |
| 🎨 **Whiteboard** | Collaborative drawing |
| 💬 **Chat** | Real-time messaging |
| 🎤 **VoIP** | Voice communication |

### 🛠️ Advanced
| Feature | Description |
|---------|-------------|
| ⚡ **Power Control** | Remote shutdown/restart |
| 🖨️ **Remote Printing** | Print to remote printers |
| 🪟 **Window Manager** | Control remote windows |
| 🎬 **Macro Recording** | Record & playback actions |
| 📊 **System Stats** | CPU/RAM/Disk monitoring |

---

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/yourusername/SpaceLink.git
cd SpaceLink

# Install dependencies
pip install -r requirements.txt

# Start server
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

Open browser: `http://localhost:8000/webrtc-test`

---

## 📦 Architecture

```
SpaceLink/
├── server.py              # FastAPI main server
├── webrtc_server.py       # WebRTC handling
├── webrtc_client.html     # Web client (2000+ lines)
├── SpaceLinkClient.swift  # iOS client
│
├── 🔧 Core Modules
│   ├── input_control.py   # Mouse/keyboard control
│   ├── ai_agent.py        # AI command processing
│   └── screen_capture.py  # Screen capture
│
├── 📁 File & Clipboard
│   ├── file_transfer.py   # File management
│   └── clipboard_sync.py  # Clipboard sync
│
├── ⚡ Performance
│   ├── codec_manager.py   # Codec selection
│   ├── network_optimizer.py # Network optimization
│   └── hw_encoder.py      # Hardware encoding
│
├── 🔒 Security
│   ├── auth.py            # Authentication
│   ├── security.py        # AES & 2FA
│   └── audit_log.py       # Audit logging
│
├── 🤝 Collaboration
│   ├── collaboration.py   # Multi-user
│   ├── whiteboard.py      # Drawing
│   └── voip.py            # Voice chat
│
└── 🛠️ Utilities
    ├── power_control.py   # Power management
    ├── system_stats.py    # System monitoring
    ├── window_manager.py  # Window control
    ├── tts.py             # Text-to-speech
    ├── remote_print.py    # Printing
    └── macro_recorder.py  # Macros
```

---

## 📖 Documentation

- [📥 Installation Guide](INSTALLATION.md)
- [✨ Features Documentation](FEATURES.md)
- [🔌 API Reference](API.md)

---

## 🔧 Requirements

- Python 3.8+
- FFmpeg (for hardware encoding)
- Modern web browser (Chrome/Firefox/Edge)

---

## 📊 API Endpoints

SpaceLink provides **120+ REST API endpoints**:

| Category | Endpoints |
|----------|-----------|
| WebRTC | `/offer`, `/answer`, `/ice` |
| Files | `/files/*` |
| Clipboard | `/clipboard/*` |
| Power | `/power/*` |
| Stats | `/stats/*` |
| Macros | `/macro/*` |
| Windows | `/windows/*` |
| TTS | `/tts/*` |
| Optimization | `/optimize/*` |
| Audit | `/audit/*` |
| Whiteboard | `/whiteboard/*` |
| Collaboration | `/collab/*` |
| Print | `/print/*` |
| VoIP | `/voip/*` |

---

## 🖼️ Screenshots

<p align="center">
  <em>Web Client Interface</em>
</p>

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

---

## 🙏 Acknowledgments

Inspired by:
- [Parsec](https://parsec.app) - Low latency gaming
- [AnyDesk](https://anydesk.com) - Fast remote desktop
- [TeamViewer](https://teamviewer.com) - Enterprise collaboration

---

<p align="center">
  Made with ❤️ by the SpaceLink Team
</p>
