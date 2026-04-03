"""
FastAPI Server for Jarvis HR Agent
Replaces eel. Handles WebSocket communication, STT, TTS, and feature routing.
"""

import json
import logging
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.command import transcribe_audio, text_to_speech
from backend.config import FRONTEND_ORIGIN
from backend.db import log_conversation
from backend.feature import handle_user_text
from backend.feedback import StatusIndicator

logger = logging.getLogger(__name__)

app = FastAPI(title="Jarvis HR Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "online", "agent": "Jarvis HR Agent"}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    session_id = str(uuid.uuid4())
    StatusIndicator.info(f"WebSocket connected. Session: {session_id}")

    try:
        while True:
            # Receive message — can be JSON (text command) or bytes (audio)
            message = await ws.receive()

            user_text = ""
            language = "en"

            # ── Audio input ────────────────────────────────────────────────
            if "bytes" in message and message["bytes"]:
                audio_bytes = message["bytes"]
                result = await transcribe_audio(audio_bytes)
                user_text = result["text"]
                language = result.get("language", "en")

                if not user_text:
                    await ws.send_json({"type": "error", "text": "Could not transcribe audio."})
                    continue

                # Send transcript back so UI can display it
                await ws.send_json({
                    "type": "transcript",
                    "text": user_text,
                    "language": language,
                })

            # ── Text input ─────────────────────────────────────────────────
            elif "text" in message and message["text"]:
                try:
                    data = json.loads(message["text"])
                    user_text = data.get("text", "")
                    language = data.get("language", "en")
                except (json.JSONDecodeError, KeyError):
                    user_text = message["text"]

            if not user_text:
                continue

            # ── Feature execution ──────────────────────────────────────────
            StatusIndicator.processing(f"Executing: {user_text}")
            response_text = await handle_user_text(user_text, language)

            # ── Send text response ─────────────────────────────────────────
            await ws.send_json({
                "type": "response",
                "text": response_text,
                "language": language,
            })

            # ── Generate and send audio ────────────────────────────────────
            audio_bytes = await text_to_speech(response_text, language)
logger.info(f"TTS audio size: {len(audio_bytes)} bytes")
if audio_bytes:
    await ws.send_bytes(audio_bytes)
else:
    logger.error("TTS returned empty audio — check SARVAM_API_KEY")

            # ── Log to Supabase ────────────────────────────────────────────
            await log_conversation(user_text, response_text, language)

    except WebSocketDisconnect:
        StatusIndicator.info(f"WebSocket disconnected. Session: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await ws.send_json({"type": "error", "text": "Internal server error."})
        except Exception:
            pass
