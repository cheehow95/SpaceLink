"""
Text-to-Speech Module for SpaceLink
Read text aloud on the remote PC.
"""
import sys
import threading


def speak(text: str, rate: int = 150, volume: float = 1.0) -> dict:
    """Speak text using system TTS."""
    try:
        if sys.platform == "win32":
            # Use Windows SAPI
            def _speak():
                import win32com.client
                speaker = win32com.client.Dispatch("SAPI.SpVoice")
                speaker.Rate = (rate - 150) // 25  # Convert to SAPI rate (-10 to 10)
                speaker.Volume = int(volume * 100)
                speaker.Speak(text)
            
            thread = threading.Thread(target=_speak, daemon=True)
            thread.start()
            
        elif sys.platform == "darwin":
            import os
            os.system(f'say "{text}"')
            
        else:
            # Linux with espeak
            import os
            os.system(f'espeak "{text}"')
        
        return {"status": "ok", "message": f"Speaking: {text[:30]}..."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def stop_speaking() -> dict:
    """Stop any ongoing speech (Windows only)."""
    try:
        if sys.platform == "win32":
            import win32com.client
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            speaker.Speak("", 3)  # SVSFPurgeBeforeSpeak
        return {"status": "ok", "message": "Speech stopped"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_voices() -> list:
    """Get available TTS voices (Windows only)."""
    voices = []
    try:
        if sys.platform == "win32":
            import win32com.client
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            for voice in speaker.GetVoices():
                voices.append({
                    "name": voice.GetDescription(),
                    "id": voice.Id
                })
    except:
        pass
    return voices
