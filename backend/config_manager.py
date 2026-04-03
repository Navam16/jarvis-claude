"""
Configuration Management Module for Jarvis HR Agent
Web deployment version - Render + Supabase + Groq + Sarvam AI
"""

import logging
import os
from pathlib import Path
from typing import Optional


class Config:
    """Configuration management for Jarvis HR Agent (web deployment)"""

    def __init__(self, env_file: str = ".env"):
        self.env_file = env_file
        self._load_env_file()
        self._setup_logging()

    def _load_env_file(self):
        """Load environment variables from .env file if it exists"""
        env_path = Path(self.env_file)
        if env_path.exists():
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()

    def _setup_logging(self):
        """Setup logging configuration"""
        log_level = self.get("LOG_LEVEL", "INFO")
        Path("logs").mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("logs/jarvis.log"),
                logging.StreamHandler()
            ],
        )

    def get(self, key: str, default: Optional[str] = None) -> str:
        return os.environ.get(key, default)

    def get_bool(self, key: str, default: bool = False) -> bool:
        value = self.get(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")

    def get_int(self, key: str, default: int = 0) -> int:
        try:
            return int(self.get(key, str(default)))
        except ValueError:
            return default

    def get_float(self, key: str, default: float = 0.0) -> float:
        try:
            return float(self.get(key, str(default)))
        except ValueError:
            return default

    # ── Application ──────────────────────────────────────────────────────────
    @property
    def assistant_name(self) -> str:
        return self.get("ASSISTANT_NAME", "jarvis")

    @property
    def app_name(self) -> str:
        return self.get("APP_NAME", "Jarvis HR Agent")

    @property
    def debug_mode(self) -> bool:
        return self.get_bool("DEBUG_MODE", False)

    # ── Supabase ─────────────────────────────────────────────────────────────
    @property
    def supabase_url(self) -> str:
        return self.get("SUPABASE_URL", "")

    @property
    def supabase_key(self) -> str:
        return self.get("SUPABASE_KEY", "")

    @property
    def supabase_service_key(self) -> str:
        return self.get("SUPABASE_SERVICE_KEY", "")

    # ── Groq (LLM + STT) ─────────────────────────────────────────────────────
    @property
    def groq_api_key(self) -> str:
        return self.get("GROQ_API_KEY", "")

    @property
    def groq_model(self) -> str:
        return self.get("GROQ_MODEL", "llama-3.3-70b-versatile")

    @property
    def groq_whisper_model(self) -> str:
        return self.get("GROQ_WHISPER_MODEL", "whisper-large-v3")

    # ── Sarvam AI (TTS) ───────────────────────────────────────────────────────
    @property
    def sarvam_api_key(self) -> str:
        return self.get("SARVAM_API_KEY", "")

    @property
    def sarvam_speaker(self) -> str:
        return self.get("SARVAM_SPEAKER", "meera")

    @property
    def sarvam_model(self) -> str:
        return self.get("SARVAM_MODEL", "bulbul:v1")

    # ── External APIs ─────────────────────────────────────────────────────────
    @property
    def openweathermap_api_key(self) -> str:
        return self.get("OPENWEATHERMAP_API_KEY", "")

    @property
    def news_api_key(self) -> str:
        return self.get("NEWS_API_KEY", "")

    # ── Server ────────────────────────────────────────────────────────────────
    @property
    def web_server_host(self) -> str:
        return self.get("WEB_SERVER_HOST", "0.0.0.0")

    @property
    def web_server_port(self) -> int:
        return self.get_int("WEB_SERVER_PORT", 8000)

    @property
    def frontend_origin(self) -> str:
        return self.get("FRONTEND_ORIGIN", "*")

    # ── User ──────────────────────────────────────────────────────────────────
    @property
    def user_name(self) -> str:
        return self.get("USER_NAME", "User")


# Global config instance
config = Config()


# Convenience helpers
def get_config(key: str, default: Optional[str] = None) -> str:
    return config.get(key, default)

def get_config_bool(key: str, default: bool = False) -> bool:
    return config.get_bool(key, default)

def get_config_int(key: str, default: int = 0) -> int:
    return config.get_int(key, default)
