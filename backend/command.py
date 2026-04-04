"""
Command Module for Jarvis HR Agent
Web deployment version:
  - STT: Groq Whisper
  - TTS: Sarvam AI
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

groq_client = Groq(api_key=GROQ_API_KEY)

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


async def transcribe_audio(audio_bytes: bytes) -> dict:
    """Transcribe audio bytes using Groq Whisper."""
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


async def text_to_speech(text: str, language: str = "en") -> bytes:
    """Convert text to speech using Sarvam AI."""
    if not text:
        return b""

    lang_code = LANG_CODE_MAP.get(language, "en-IN")
    StatusIndicator.processing(f"Sarvam TTS [{lang_code}]: {text[:60]}...")

    payload = {
        "inputs": [text],
        "target_language_code": lang_code,
        "speaker": "anushka",
        "model": "bulbul:v3",
        "pace": 1.0,
        "enable_preprocessing": True,
        "audio_format": "wav",
    }

    logger.info(f"Sarvam request — model: {"bulbul:v3"}, speaker: {"anushka"}, lang: {lang_code}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.sarvam.ai/text-to-speech",
                headers={
                    "api-subscription-key": SARVAM_API_KEY,
                    "Content-Type": "application/json",
                },
                json=payload,
            )

            logger.info(f"Sarvam response status: {response.status_code}")
            logger.info(f"Sarvam response body: {response.text[:500]}")

            response.raise_for_status()
            data = response.json()
            audio_bytes = base64.b64decode(data["audios"][0])
            StatusIndicator.success(f"TTS audio generated: {len(audio_bytes)} bytes")
            return audio_bytes

    except httpx.HTTPStatusError as e:
        logger.error(f"Sarvam HTTP error {e.response.status_code}: {e.response.text}")
        return b""
    except Exception as e:
        logger.error(f"Sarvam TTS error: {e}")
        return b""


def speak(text: str) -> str:
    """Log response text. Actual audio is sent over WebSocket by server.py."""
    text = str(text)
    StatusIndicator.response(text)
    return text
