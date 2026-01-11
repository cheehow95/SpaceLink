from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, UploadFile, File, Form
from fastapi.responses import StreamingResponse, HTMLResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import json
import asyncio
import io
import os

from modules.stream_capture import ScreenCapture
from core.input_control import execute_command
from core.ai_agent import AIAgent
from core.webrtc_server import webrtc_manager

# Import new enhancement modules
from modules.file_transfer import file_manager
from modules.clipboard_sync import clipboard_manager
from modules.session_manager import session_manager
from modules.recorder import screen_recorder
from modules.wol import wol_manager
from modules.hw_encoder import hw_encoder_manager
from security.auth import get_auth_status, set_password, verify_password, create_token, verify_token
import utils.power_control as power_control
import utils.system_stats as system_stats
from utils.macro_recorder import macro_recorder
import utils.window_manager as window_manager
import utils.tts as tts

# v4.0 optimization modules
from utils.codec_manager import codec_manager, get_codec_status
from utils.network_optimizer import network_optimizer, optimize_network, get_network_status
from security.security import security_manager, get_security_status, setup_2fa, verify_2fa

# v4.1 advanced modules
from security.audit_log import audit_log, log_event, get_audit_entries, get_audit_stats
from collaboration.whiteboard import whiteboard
from collaboration.collaboration import collab_session, join_session, leave_session, get_session_users
import utils.remote_print as remote_print
import collaboration.voip as voip

app = FastAPI(title="SpaceLink PC Agent", version="4.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
screen_capture = ScreenCapture()
ai_agent = AIAgent()

# Store active WebRTC peer connections
active_pcs = {}

# Video quality settings
video_settings = {
    "fps": 15,
    "quality": 50,
    "max_width": 1280,
    "resize_factor": 0.6
}

# ============ Pydantic Models ============

class VideoSettings(BaseModel):
    fps: int = 15
    quality: int = 50
    max_width: int = 1280

class ClipboardData(BaseModel):
    content_type: str
    data: str

class FileWriteData(BaseModel):
    path: str
    content: str
    encoding: str = "base64"
    append: bool = False

class SessionSettings(BaseModel):
    fps: Optional[int] = None
    max_width: Optional[int] = None
    audio_enabled: Optional[bool] = None
    audio_muted: Optional[bool] = None
    volume: Optional[float] = None
    selected_monitor: Optional[int] = None

class WoLDevice(BaseModel):
    name: str
    mac_address: str
    description: str = ""
    broadcast_ip: str = "255.255.255.255"

# ============ Root & Info ============

@app.get("/")
async def root():
    return {
        "message": "SpaceLink PC Agent is Online",
        "version": "3.1",
        "features": [
            "mjpeg_stream", "websocket_control", "webrtc", "ai_agent",
            "video_settings", "audio_streaming", "file_transfer",
            "clipboard_sync", "multi_monitor", "session_persistence",
            "screen_recording", "wake_on_lan", "hardware_encoding",
            "authentication", "screenshot", "pip", "latency_tracking"
        ],
        "auth": get_auth_status()
    }

# ============ Video Settings ============

@app.get("/settings/video")
async def get_video_settings():
    """Get current video settings."""
    return video_settings

@app.post("/settings/video")
async def update_video_settings(settings: VideoSettings):
    """Update video settings."""
    global video_settings
    video_settings["fps"] = max(5, min(60, settings.fps))
    video_settings["quality"] = max(10, min(100, settings.quality))
    video_settings["max_width"] = max(640, min(3840, settings.max_width))
    
    # Update WebRTC manager settings
    webrtc_manager.update_settings(
        fps=video_settings["fps"],
        max_width=video_settings["max_width"]
    )
    
    return {"status": "updated", "settings": video_settings}

# ============ Audio Settings ============

@app.get("/settings/audio")
async def get_audio_settings():
    """Get audio settings."""
    from modules.audio_capture import audio_manager
    return {
        "muted": audio_manager.muted,
        "volume": audio_manager.volume,
        "devices": audio_manager.get_available_devices()
    }

@app.post("/settings/audio")
async def update_audio_settings(request: Request):
    """Update audio settings."""
    from modules.audio_capture import audio_manager
    data = await request.json()
    
    if "muted" in data:
        audio_manager.set_muted(data["muted"])
    if "volume" in data:
        audio_manager.set_volume(data["volume"])
    
    return {"status": "ok", "muted": audio_manager.muted, "volume": audio_manager.volume}

# ============ Encoder Settings ============

@app.get("/settings/encoder")
async def get_encoder_settings():
    """Get available encoders and current selection."""
    return {
        "encoders": hw_encoder_manager.get_available_encoders(),
        "selected": hw_encoder_manager.get_selected_encoder(),
        "gpu_info": hw_encoder_manager.get_gpu_info()
    }

@app.post("/settings/encoder")
async def set_encoder(request: Request):
    """Select an encoder."""
    data = await request.json()
    encoder_name = data.get("encoder")
    if encoder_name:
        return hw_encoder_manager.select_encoder(encoder_name)
    return {"status": "error", "message": "No encoder specified"}

# ============ MJPEG Streaming (Local Network) ============

@app.get("/stream")
def video_feed():
    """MJPEG Streaming Endpoint for local network."""
    return StreamingResponse(
        screen_capture.generate_jpeg_stream(
            quality=video_settings["quality"], 
            resize_factor=video_settings["resize_factor"]
        ),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

# ============ WebSocket Control (Local Network) ============

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("[WS] Client connected")
    try:
        while True:
            data = await websocket.receive_text()
            try:
                command = json.loads(data)
                
                if "prompt" in command:
                    print(f"[WS] AI Prompt: {command['prompt']}")
                    action_cmd = ai_agent.process_command(command['prompt'])
                    if action_cmd.get("status") != "error":
                        result = execute_command(action_cmd)
                        await websocket.send_text(json.dumps(result))
                    else:
                        await websocket.send_text(json.dumps(action_cmd))
                else:
                    result = execute_command(command)
                    await websocket.send_text(json.dumps(result))
                
            except json.JSONDecodeError:
                print("[WS] Failed to decode JSON")
            except Exception as e:
                print(f"[WS] Error: {e}")
                
    except WebSocketDisconnect:
        print("[WS] Client disconnected")

# ============ WebRTC Signaling (Internet) ============

@app.post("/webrtc/offer")
async def create_webrtc_offer():
    """Create a WebRTC offer. The PC initiates the connection."""
    try:
        offer, pc = await webrtc_manager.create_offer()
        pc_id = str(id(pc))
        active_pcs[pc_id] = pc
        return {"offer": offer, "pc_id": pc_id}
    except Exception as e:
        print(f"[WebRTC] Error creating offer: {e}")
        return {"error": str(e)}

@app.post("/webrtc/answer")
async def receive_webrtc_answer(request: Request):
    """Receive the answer from the client to complete the connection."""
    try:
        data = await request.json()
        pc_id = data.get("pc_id")
        answer = data.get("answer")
        
        if pc_id not in active_pcs:
            return {"error": "Invalid pc_id"}
        
        pc = active_pcs[pc_id]
        await webrtc_manager.handle_answer(pc, answer)
        return {"status": "connected"}
    except Exception as e:
        print(f"[WebRTC] Error handling answer: {e}")
        return {"error": str(e)}

@app.post("/webrtc/connect")
async def handle_client_offer(request: Request):
    """Handle an offer from a client (client initiates)."""
    try:
        data = await request.json()
        offer = data.get("offer")
        
        answer, pc = await webrtc_manager.handle_offer(offer)
        pc_id = str(id(pc))
        active_pcs[pc_id] = pc
        
        return {"answer": answer, "pc_id": pc_id}
    except Exception as e:
        print(f"[WebRTC] Error handling offer: {e}")
        return {"error": str(e)}

# ============ Multi-Monitor Support ============

@app.get("/monitors/list")
async def list_monitors():
    """List available monitors."""
    return {
        "status": "ok",
        "monitors": screen_capture.enumerate_monitors(),
        "count": screen_capture.monitor_count
    }

@app.get("/monitors/current")
async def get_current_monitor():
    """Get currently selected monitor."""
    return screen_capture.get_current_monitor()

@app.post("/monitors/select")
async def select_monitor(request: Request):
    """Select a monitor for capture."""
    data = await request.json()
    monitor_index = data.get("index", 1)
    result = screen_capture.select_monitor(monitor_index)
    
    # Update WebRTC if needed
    if result.get("status") == "ok":
        webrtc_manager.screen_capture = screen_capture
    
    return result

# ============ File Transfer ============

@app.get("/files/drives")
async def list_drives():
    """List available drives/mount points."""
    return file_manager.get_drives()

@app.get("/files/list")
async def list_files(path: Optional[str] = None):
    """List files in directory."""
    return file_manager.list_files(path)

@app.get("/files/read")
async def read_file(path: str):
    """Read file content."""
    return file_manager.read_file(path)

@app.get("/files/download")
async def download_file(path: str):
    """Download a file."""
    from pathlib import Path
    file_path = Path(path)
    if file_path.exists() and file_path.is_file():
        return FileResponse(
            path=str(file_path),
            filename=file_path.name,
            media_type="application/octet-stream"
        )
    return {"status": "error", "message": "File not found"}

@app.post("/files/write")
async def write_file(data: FileWriteData):
    """Write content to file."""
    return file_manager.write_file(data.path, data.content, data.encoding, data.append)

@app.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    path: Optional[str] = Form(None)
):
    """Upload a file."""
    import base64
    from pathlib import Path
    
    # Determine destination
    dest_dir = Path(path) if path else file_manager.base_dir
    dest_path = dest_dir / file.filename
    
    try:
        content = await file.read()
        with open(dest_path, 'wb') as f:
            f.write(content)
        
        return {
            "status": "ok",
            "path": str(dest_path),
            "size": len(content)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.delete("/files/delete")
async def delete_file(path: str):
    """Delete a file."""
    return file_manager.delete_file(path)

@app.post("/files/mkdir")
async def create_directory(request: Request):
    """Create a directory."""
    data = await request.json()
    return file_manager.create_directory(data.get("path", ""))

# ============ Clipboard Sync ============

@app.get("/clipboard")
async def get_clipboard():
    """Get current clipboard content."""
    return clipboard_manager.get_clipboard()

@app.post("/clipboard")
async def set_clipboard(data: ClipboardData):
    """Set clipboard content."""
    return clipboard_manager.set_clipboard(data.content_type, data.data)

# ============ Session Management ============

@app.post("/session/create")
async def create_session(request: Request):
    """Create a new session."""
    data = await request.json() if await request.body() else {}
    return session_manager.create_session(data.get("client_info"))

@app.post("/session/resume")
async def resume_session(request: Request):
    """Resume an existing session."""
    data = await request.json()
    session_id = data.get("session_id")
    if not session_id:
        return {"status": "error", "message": "session_id required"}
    return session_manager.resume_session(session_id)

@app.post("/session/update")
async def update_session(request: Request):
    """Update session settings."""
    data = await request.json()
    session_id = data.get("session_id")
    settings = data.get("settings")
    return session_manager.update_session(session_id, settings=settings)

@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get session info."""
    return session_manager.get_session(session_id) or {"status": "error", "message": "Session not found"}

@app.delete("/session/{session_id}")
async def end_session(session_id: str):
    """End a session."""
    return session_manager.end_session(session_id)

@app.get("/sessions")
async def list_sessions():
    """List active sessions."""
    return session_manager.get_active_sessions()

# ============ Screen Recording ============

@app.get("/recording/status")
async def recording_status():
    """Get recording status."""
    return screen_recorder.get_status()

@app.post("/recording/start")
async def start_recording(request: Request):
    """Start recording."""
    data = await request.json() if await request.body() else {}
    return screen_recorder.start_recording(
        filename=data.get("filename"),
        fps=data.get("fps", 30)
    )

@app.post("/recording/stop")
async def stop_recording():
    """Stop recording."""
    return screen_recorder.stop_recording()

@app.post("/recording/pause")
async def pause_recording():
    """Pause recording."""
    return screen_recorder.pause_recording()

@app.post("/recording/resume")
async def resume_recording():
    """Resume recording."""
    return screen_recorder.resume_recording()

@app.get("/recording/list")
async def list_recordings():
    """List available recordings."""
    return screen_recorder.list_recordings()

@app.get("/recording/download")
async def download_recording(filename: str):
    """Download a recording."""
    from pathlib import Path
    filepath = screen_recorder.output_dir / filename
    if filepath.exists():
        return FileResponse(
            path=str(filepath),
            filename=filename,
            media_type="video/mp4"
        )
    return {"status": "error", "message": "Recording not found"}

@app.delete("/recording/{filename}")
async def delete_recording(filename: str):
    """Delete a recording."""
    return screen_recorder.delete_recording(filename)

# ============ Wake-on-LAN ============

@app.get("/wol/info")
async def wol_info():
    """Get WoL info including this PC's MAC."""
    return {
        "this_pc_mac": wol_manager.get_this_pc_mac(),
        "local_info": wol_manager.get_local_info(),
        "saved_devices": wol_manager.get_saved_devices()
    }

@app.post("/wol/wake")
async def wake_device(request: Request):
    """Send WoL magic packet."""
    data = await request.json()
    return wol_manager.wake(
        mac_address=data.get("mac_address"),
        device_name=data.get("device_name"),
        broadcast_ip=data.get("broadcast_ip", "255.255.255.255")
    )

@app.post("/wol/device")
async def save_wol_device(device: WoLDevice):
    """Save a WoL device."""
    return wol_manager.save_device(
        device.name,
        device.mac_address,
        device.description,
        device.broadcast_ip
    )

@app.delete("/wol/device/{name}")
async def remove_wol_device(name: str):
    """Remove a saved WoL device."""
    return wol_manager.remove_device(name)

# ============ QR Code for Easy Pairing ============

@app.get("/qr")
async def get_connection_qr(request: Request):
    """Generate a QR code containing connection info."""
    import qrcode
    from PIL import Image
    
    connection_info = {
        "type": "spacelink",
        "host": str(request.base_url).rstrip("/"),
        "webrtc": True,
        "version": "3.0",
        "mac": wol_manager.get_this_pc_mac()
    }
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(json.dumps(connection_info))
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    
    return Response(content=img_bytes.getvalue(), media_type="image/png")

@app.get("/webrtc-test")
async def webrtc_test_page():
    """Serve the WebRTC test client."""
    return HTMLResponse(open("webrtc_client.html", "r", encoding="utf-8").read())

# ============ Power Control ============

class PowerAction(BaseModel):
    delay: int = 0
    force: bool = False

@app.post("/power/shutdown")
async def api_shutdown(action: PowerAction = PowerAction()):
    return power_control.shutdown(action.delay, action.force)

@app.post("/power/restart")
async def api_restart(action: PowerAction = PowerAction()):
    return power_control.restart(action.delay, action.force)

@app.post("/power/cancel")
async def api_cancel_shutdown():
    return power_control.cancel_shutdown()

@app.post("/power/lock")
async def api_lock():
    return power_control.lock_screen()

@app.post("/power/sleep")
async def api_sleep():
    return power_control.sleep()

@app.post("/power/hibernate")
async def api_hibernate():
    return power_control.hibernate()

@app.get("/power/info")
async def api_system_info():
    return power_control.get_system_info()

# ============ System Stats ============

@app.get("/stats")
async def api_all_stats():
    """Get all system stats."""
    return system_stats.get_all_stats()

@app.get("/stats/cpu")
async def api_cpu_stats():
    return system_stats.get_cpu_usage()

@app.get("/stats/memory")
async def api_memory_stats():
    return system_stats.get_memory_usage()

@app.get("/stats/disk")
async def api_disk_stats():
    return system_stats.get_disk_usage()

@app.get("/stats/network")
async def api_network_stats():
    return system_stats.get_network_stats()

@app.get("/stats/processes")
async def api_processes():
    return system_stats.get_top_processes(10)

@app.get("/stats/battery")
async def api_battery():
    return system_stats.get_battery()

# ============ Macros ============

class MacroName(BaseModel):
    name: str = ""

@app.post("/macro/start")
async def api_macro_start(data: MacroName = MacroName()):
    return macro_recorder.start_recording(data.name if data.name else None)

@app.post("/macro/stop")
async def api_macro_stop():
    return macro_recorder.stop_recording()

@app.get("/macro/list")
async def api_macro_list():
    return macro_recorder.get_macros()

@app.get("/macro/{name}")
async def api_macro_get(name: str):
    return macro_recorder.load_macro(name)

@app.delete("/macro/{name}")
async def api_macro_delete(name: str):
    return macro_recorder.delete_macro(name)

@app.get("/macro/status")
async def api_macro_status():
    return {"recording": macro_recorder.is_recording()}

# ============ Clipboard History ============

clipboard_history = []
MAX_CLIPBOARD_HISTORY = 10

@app.get("/clipboard/history")
async def api_clipboard_history():
    return {"history": clipboard_history[-MAX_CLIPBOARD_HISTORY:]}

@app.post("/clipboard/history/add")
async def api_clipboard_history_add():
    """Add current clipboard to history."""
    content = clipboard_manager.get_clipboard()
    if content.get("data"):
        clipboard_history.append({
            "type": content.get("content_type"),
            "data": content.get("data")[:100],  # Truncate for preview
            "timestamp": __import__("datetime").datetime.now().isoformat()
        })
        if len(clipboard_history) > MAX_CLIPBOARD_HISTORY:
            clipboard_history.pop(0)
    return {"status": "ok", "count": len(clipboard_history)}

# ============ Window Manager ============

@app.get("/windows")
async def api_get_windows():
    """Get list of open windows."""
    return window_manager.get_windows()

@app.post("/windows/{hwnd}/focus")
async def api_focus_window(hwnd: int):
    return window_manager.focus_window(hwnd)

@app.post("/windows/{hwnd}/minimize")
async def api_minimize_window(hwnd: int):
    return window_manager.minimize_window(hwnd)

@app.post("/windows/{hwnd}/maximize")
async def api_maximize_window(hwnd: int):
    return window_manager.maximize_window(hwnd)

@app.post("/windows/{hwnd}/close")
async def api_close_window(hwnd: int):
    return window_manager.close_window(hwnd)

# ============ Text-to-Speech ============

class TTSRequest(BaseModel):
    text: str
    rate: int = 150
    volume: float = 1.0

@app.post("/tts/speak")
async def api_speak(req: TTSRequest):
    return tts.speak(req.text, req.rate, req.volume)

@app.post("/tts/stop")
async def api_stop_speaking():
    return tts.stop_speaking()

@app.get("/tts/voices")
async def api_get_voices():
    return tts.get_voices()

# ============ QR Code Connection ============

@app.get("/qr")
async def api_qr_code():
    """Generate QR code for easy mobile connection."""
    import qrcode
    import socket
    from io import BytesIO
    
    # Get local IP
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    url = f"http://{local_ip}:8000/webrtc-test"
    
    qr = qrcode.make(url)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)
    
    return Response(content=buffer.getvalue(), media_type="image/png")

# ============ v4.0 Optimization APIs ============

@app.get("/optimize/codec")
async def api_get_codec_status():
    """Get codec manager status and recommendations."""
    return get_codec_status()

@app.get("/optimize/network")
async def api_get_network_status():
    """Get network optimizer status."""
    return get_network_status()

@app.post("/optimize/network/update")
async def api_update_network(latency: float = 50, packet_loss: float = 0, bandwidth: float = 5000):
    """Update network metrics and get recommendations."""
    return optimize_network(latency, packet_loss, bandwidth)

@app.get("/optimize/security")
async def api_get_security_status():
    """Get security module status."""
    return get_security_status()

@app.post("/optimize/2fa/setup")
async def api_setup_2fa(user_id: str = "default"):
    """Setup 2FA for a user."""
    return setup_2fa(user_id)

class TwoFAVerify(BaseModel):
    user_id: str = "default"
    code: str

@app.post("/optimize/2fa/verify")
async def api_verify_2fa(data: TwoFAVerify):
    """Verify 2FA code."""
    return {"verified": verify_2fa(data.user_id, data.code)}

# ============ v4.1 Advanced Features ============

# Audit Log
@app.get("/audit/entries")
async def api_audit_entries(limit: int = 50):
    return get_audit_entries(limit)

@app.get("/audit/stats")
async def api_audit_stats():
    return get_audit_stats()

# Whiteboard
class WhiteboardDraw(BaseModel):
    action: str  # line, circle, rect, text, erase
    x1: float
    y1: float
    x2: float = 0
    y2: float = 0
    color: str = "#ffffff"
    thickness: int = 2
    text: str = ""

@app.post("/whiteboard/draw")
async def api_whiteboard_draw(data: WhiteboardDraw):
    if data.action == "line":
        return whiteboard.draw_line(data.x1, data.y1, data.x2, data.y2, data.color, data.thickness)
    elif data.action == "circle":
        return whiteboard.draw_circle(data.x1, data.y1, data.x2, data.color, data.thickness)
    elif data.action == "rect":
        return whiteboard.draw_rect(data.x1, data.y1, data.x2, data.y2, data.color, data.thickness)
    elif data.action == "text":
        return whiteboard.add_text(data.x1, data.y1, data.text, data.color)
    elif data.action == "erase":
        return whiteboard.erase(data.x1, data.y1, data.x2)
    return {"status": "error", "message": "Unknown action"}

@app.get("/whiteboard/actions")
async def api_whiteboard_get(since: float = 0):
    return whiteboard.get_actions(since)

@app.post("/whiteboard/undo")
async def api_whiteboard_undo():
    return whiteboard.undo()

@app.post("/whiteboard/redo")
async def api_whiteboard_redo():
    return whiteboard.redo()

@app.post("/whiteboard/clear")
async def api_whiteboard_clear():
    return whiteboard.clear()

@app.get("/whiteboard/export")
async def api_whiteboard_export():
    svg = whiteboard.export_svg()
    return Response(content=svg, media_type="image/svg+xml")

# Collaboration
class JoinSession(BaseModel):
    display_name: str
    role: str = "viewer"

@app.post("/collab/join")
async def api_collab_join(data: JoinSession):
    return join_session(data.display_name, data.role)

@app.post("/collab/leave/{user_id}")
async def api_collab_leave(user_id: str):
    return leave_session(user_id)

@app.get("/collab/users")
async def api_collab_users():
    return get_session_users()

@app.get("/collab/status")
async def api_collab_status():
    return collab_session.get_status()

class CursorUpdate(BaseModel):
    user_id: str
    x: float
    y: float

@app.post("/collab/cursor")
async def api_collab_cursor(data: CursorUpdate):
    return collab_session.update_cursor(data.user_id, data.x, data.y)

@app.get("/collab/cursors")
async def api_collab_cursors():
    return collab_session.get_cursors()

class ChatMessage(BaseModel):
    user_id: str
    message: str

@app.post("/collab/chat")
async def api_collab_chat(data: ChatMessage):
    return collab_session.send_chat(data.user_id, data.message)

@app.get("/collab/chat")
async def api_collab_get_chat(limit: int = 50):
    return collab_session.get_chat(limit)

# Remote Printing
@app.get("/print/printers")
async def api_get_printers():
    return remote_print.get_printers()

@app.get("/print/status")
async def api_print_status():
    return remote_print.get_status()

class PrintText(BaseModel):
    text: str
    printer: str = None

@app.post("/print/text")
async def api_print_text(data: PrintText):
    return remote_print.print_text(data.text, data.printer)

# VoIP
@app.get("/voip/devices")
async def api_voip_devices():
    return voip.get_audio_devices()

@app.get("/voip/status")
async def api_voip_status():
    return voip.get_voip_status()

@app.post("/voip/start")
async def api_voip_start(device_id: int = None):
    return voip.start_voice_capture(device_id)

@app.post("/voip/stop")
async def api_voip_stop():
    return voip.stop_voice_capture()

@app.post("/voip/mute")
async def api_voip_mute(muted: bool = True):
    return voip.voip_manager.set_mute(muted)

@app.post("/voip/volume")
async def api_voip_volume(volume: float = 1.0):
    return voip.voip_manager.set_volume(volume)

@app.on_event("shutdown")
async def shutdown_event():
    await webrtc_manager.cleanup_all()
    session_manager.shutdown()
    print("[Server] Cleaned up WebRTC connections and sessions")
