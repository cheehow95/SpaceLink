# 📥 Installation Guide

## Prerequisites

### Required
- **Python 3.8+** - [Download](https://python.org)
- **FFmpeg** - [Download](https://ffmpeg.org)
- Modern web browser (Chrome, Firefox, Edge)

### Optional
- NVIDIA GPU (for NVENC hardware encoding)
- AMD GPU (for AMF hardware encoding)
- Intel CPU with integrated graphics (for QuickSync)

---

## 🚀 Quick Installation

### Windows

```powershell
# Clone repository
git clone https://github.com/yourusername/SpaceLink.git
cd SpaceLink

# Create virtual environment (recommended)
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start server
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

### macOS

```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install FFmpeg
brew install ffmpeg

# Clone and setup
git clone https://github.com/yourusername/SpaceLink.git
cd SpaceLink
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start server
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

### Linux (Ubuntu/Debian)

```bash
# Install system dependencies
sudo apt update
sudo apt install python3-pip python3-venv ffmpeg

# Clone and setup
git clone https://github.com/yourusername/SpaceLink.git
cd SpaceLink
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start server
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

---

## 🔧 FFmpeg Installation

### Windows
1. Download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/)
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to PATH

### macOS
```bash
brew install ffmpeg
```

### Linux
```bash
sudo apt install ffmpeg
```

---

## 🔒 Optional: Security Setup

### Enable 2FA
```python
# In Python
from security import setup_2fa
result = setup_2fa("admin")
print(result["qr_uri"])  # Scan with Google Authenticator
```

### Set Password
```python
from auth import set_password
set_password("your-secure-password")
```

---

## 🌐 Network Configuration

### Firewall
Allow port **8000** (or your chosen port):

```powershell
# Windows
netsh advfirewall firewall add rule name="SpaceLink" dir=in action=allow protocol=TCP localport=8000
```

```bash
# Linux
sudo ufw allow 8000/tcp
```

### Port Forwarding (for external access)
Forward port **8000** on your router to your PC's local IP.

---

## ✅ Verify Installation

1. Start server: `python -m uvicorn server:app --host 0.0.0.0 --port 8000`
2. Open browser: `http://localhost:8000`
3. Check API: `http://localhost:8000/docs`
4. Web client: `http://localhost:8000/webrtc-test`

---

## 🐛 Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt --upgrade
```

### FFmpeg not found
Ensure FFmpeg is in your system PATH:
```bash
ffmpeg -version
```

### WebRTC connection fails
- Check firewall settings
- Ensure STUN/TURN servers are accessible
- Try using localhost first

### Audio not working
```bash
pip install sounddevice
```

---

## 📱 iOS Client

The Swift iOS client is in `SpaceLinkClient.swift`. To use:

1. Open in Xcode
2. Update server URL
3. Build and run on device

---

## 🔄 Updates

```bash
git pull origin main
pip install -r requirements.txt --upgrade
```
