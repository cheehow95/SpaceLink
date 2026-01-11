# ✨ SpaceLink Features Documentation

## Table of Contents
- [Core Streaming](#-core-streaming)
- [Input Control](#-input-control)
- [File & Clipboard](#-file--clipboard)
- [Performance](#-performance)
- [Security](#-security)
- [Collaboration](#-collaboration)
- [System Control](#-system-control)
- [Advanced Features](#-advanced-features)

---

## 📺 Core Streaming

### WebRTC Video
- **Protocol**: WebRTC with aiortc
- **Latency**: <50ms on LAN, <100ms on WAN
- **Resolution**: 360p to 4K
- **Frame Rate**: Up to 60 FPS

### Audio Streaming
- Bidirectional audio capture
- Sample rate: 16kHz/48kHz
- Codec: Opus

---

## 🎮 Input Control

### Mouse
| Feature | Description |
|---------|-------------|
| Click | Left, right, middle click |
| Double-click | Automatic detection |
| Drag | Hold and move |
| Scroll | Wheel and touch scroll |

### Keyboard
- Full keyboard support
- Modifier keys (Ctrl, Alt, Shift, Win)
- Function keys
- Special keys (PrintScreen, etc.)

### Gamepad
- Analog stick → Mouse movement
- A/B buttons → Left/right click
- X/Y buttons → Enter/Escape
- Bumpers → Scroll up/down

### Touch Gestures
| Gesture | Action |
|---------|--------|
| Tap | Click |
| Double tap | Double-click |
| Swipe left/right | Arrow keys |
| Swipe up/down | Scroll |
| Pinch in/out | Zoom (Ctrl +/-) |

---

## 📁 File & Clipboard

### File Transfer
- Drag & drop upload
- Browse server files
- Download files
- Size limit: 100MB per file

### Clipboard Sync
- Text synchronization
- 10-item clipboard history
- Cross-device paste

---

## ⚡ Performance

### Adaptive Bitrate
| Quality | Resolution | Bitrate | Latency Threshold |
|---------|------------|---------|-------------------|
| 4K | 3840×2160 | 15 Mbps | <20ms |
| 1440p | 2560×1440 | 8 Mbps | <50ms |
| 1080p | 1920×1080 | 5 Mbps | <100ms |
| 720p | 1280×720 | 2.5 Mbps | <150ms |
| 480p | 854×480 | 1 Mbps | <200ms |
| 360p | 640×360 | 500 Kbps | >200ms |

### Codec Priority
1. **AV1** - Best quality, high CPU
2. **H.265/HEVC** - Great quality, HW accelerated
3. **VP9** - Good compression
4. **H.264** - Wide compatibility
5. **VP8** - Fallback

### Hardware Encoding
| GPU | Encoder |
|-----|---------|
| NVIDIA | NVENC |
| AMD | AMF |
| Intel | QuickSync |

---

## 🔒 Security

### Encryption
- **AES-256-GCM** for data encryption
- **TLS 1.3** for transport
- **DTLS** for WebRTC

### Authentication
- Password protection
- API key support
- Token-based sessions
- TOTP 2FA (Google Authenticator)

### Audit Logging
- Connection events
- Command history
- Authentication attempts
- File access logs

---

## 🤝 Collaboration

### Multi-User Sessions
- Up to 10 concurrent users
- Role-based access (Host, Controller, Viewer)
- Real-time cursor sharing
- User colors for identification

### Whiteboard
- Drawing tools (line, circle, rectangle)
- Text annotations
- Eraser
- Undo/redo
- SVG export

### Chat
- Real-time messaging
- 100 message history
- User identification

### VoIP
- Voice communication
- Mute/unmute
- Volume control
- Device selection

---

## 🛠️ System Control

### Power Control
| Command | Description |
|---------|-------------|
| Lock | Lock screen |
| Sleep | Put PC to sleep |
| Hibernate | Hibernate PC |
| Restart | Restart PC (with confirmation) |
| Shutdown | Shutdown PC (with confirmation) |

### Window Manager
- List all windows
- Focus window
- Minimize/maximize
- Close window

### System Stats
- CPU usage (%)
- RAM usage (GB/%)
- Disk usage (GB/%)
- Network I/O
- Battery status
- Top processes

---

## 🔧 Advanced Features

### Text-to-Speech
- Speak text on remote PC
- Adjustable rate and volume
- Multiple voices (Windows)

### Screen Recording
- Record sessions
- Pause/resume
- List recordings

### Wake-on-LAN
- Wake remote PCs
- MAC address configuration

### Macro Recording
- Record command sequences
- Save to JSON
- Playback macros

### Quick Launch
- Predefined app buttons
- Custom favorites
- AI command support

### Remote Printing
- List printers
- Print text/files
- Default printer selection

### QR Code Connection
- Generate QR for mobile
- Easy pairing
- Local IP detection

---

## 📊 API Summary

| Category | Endpoint Count |
|----------|----------------|
| WebRTC | 5 |
| Files | 10 |
| Clipboard | 5 |
| Power | 7 |
| Stats | 8 |
| Macros | 6 |
| Windows | 5 |
| TTS | 3 |
| Optimization | 6 |
| Audit | 2 |
| Whiteboard | 7 |
| Collaboration | 8 |
| Print | 3 |
| VoIP | 6 |
| **Total** | **120+** |
