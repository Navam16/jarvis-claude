"""
Command Module for Jarvis HR Agent
Web deployment version:
  - STT: Groq Whisper (replaces SpeechRecognition + pyaudio)
  - TTS: Sarvam AI (replaces pyttsx3 + eel)
  - WebSocket: sends messages to frontend (replaces eel.expose)
"""

import base64
import logging

import httpx
from groq import Groq

from backend.config import (
    GROQ_API_KEY,
    GROQ_WHISPER_MODEL,
    SARVAM_API_KEY,
    SARVAM_MODEL,
    SARVAM_SPEAKER,
)
from backend.feedback import StatusIndicator, Timer

logger = logging.getLogger(__name__)

# ── Clients ───────────────────────────────────────────────────────────────────
groq_client = Groq(api_key=GROQ_API_KEY)

# Language code map: Whisper language → Sarvam target_language_code
LANG_CODE_MAP = {
    "hi": "hi-IN",
    "en": "en-IN",
    "mr": "mr-IN",
    "bn": "bn-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "gu": "gu-IN",
    "kn": "kn-IN",
    "pa": "pa-IN",
}


# ── STT: Groq Whisper ─────────────────────────────────────────────────────────
async def transcribe_audio(audio_bytes: bytes) -> dict:
    """
    Transcribe audio bytes using Groq Whisper.

    Args:
        audio_bytes: Raw audio bytes (webm/wav/mp3)

    Returns:
        dict with 'text' and 'language' keys
    """
    StatusIndicator.processing("Transcribing audio via Groq Whisper...")
    try:
        with Timer("Groq Whisper STT"):
            transcription = groq_client.audio.transcriptions.create(
                file=("audio.webm", audio_bytes),
                model=GROQ_WHISPER_MODEL,
                response_format="verbose_json",
            )
        language = getattr(transcription, "language", "en") or "en"
        text = transcription.text or ""
        StatusIndicator.command(f"Transcribed [{language}]: {text}")
        return {"text": text, "language": language}
    except Exception as e:
        StatusIndicator.error(f"STT failed: {e}")
        logger.error(f"Groq Whisper error: {e}")
        return {"text": "", "language": "en"}


# ── TTS: Sarvam AI ────────────────────────────────────────────────────────────
async def text_to_speech(text: str, language: str = "en") -> bytes:
    """
    Convert text to speech using Sarvam AI.
    Falls back to a silent byte string on error.

    Args:
        text: The text to speak
        language: Whisper-detected language code ('hi', 'en', etc.)

    Returns:
        Raw WAV audio bytes
    """
    if not text:
        return b""

    lang_code = LANG_CODE_MAP.get(language, "en-IN")
    StatusIndicator.processing(f"Sarvam TTS [{lang_code}]: {text[:60]}...")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.sarvam.ai/text-to-speech",
                headers={
                    "api-subscription-key": SARVAM_API_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "inputs": [text],
                    "target_language_code": lang_code,
                    "speaker": SARVAM_SPEAKER,
                    "model": SARVAM_MODEL,
                    "pitch": 0,
                    "pace": 1.0,
                    "loudness": 1.5,
                    "enable_preprocessing": True,
                    "audio_format": "wav",
                },
            )
            response.raise_for_status()
            data = response.json()
            audio_bytes = base64.b64decode(data["audios"][0])
            StatusIndicator.success("TTS audio generated.")
            return audio_bytes
    except Exception as e:
        StatusIndicator.error(f"Sarvam TTS failed: {e}")
        logger.error(f"Sarvam TTS error: {e}")
        return b""


# ── speak(): convenience wrapper used by feature.py ──────────────────────────
# In web mode, speaking is handled by the WebSocket flow in server.py.
# This function just logs the response text so existing feature.py calls
# don't break during the transition.
def speak(text: str) -> str:
    """
    Log the response text. Actual audio is generated and sent over
    WebSocket by server.py after the orchestrator returns.

    Returns the text so callers can chain / display it.
    """
    text = str(text)
    StatusIndicator.response(text)
    return text
