"""
Configuration Module for Jarvis HR Agent
Web deployment version - exports all config values from config_manager
"""

from backend.config_manager import config

# App
ASSISTANT_NAME = config.assistant_name
APP_NAME = config.app_name
DEBUG_MODE = config.debug_mode

# Supabase
SUPABASE_URL = config.supabase_url
SUPABASE_KEY = config.supabase_key
SUPABASE_SERVICE_KEY = config.supabase_service_key

# Groq
GROQ_API_KEY = config.groq_api_key
GROQ_MODEL = config.groq_model
GROQ_WHISPER_MODEL = config.groq_whisper_model

# Sarvam AI TTS
SARVAM_API_KEY = config.sarvam_api_key
SARVAM_SPEAKER = config.sarvam_speaker
SARVAM_MODEL = config.sarvam_model

# External APIs
OPENWEATHERMAP_API_KEY = config.openweathermap_api_key
NEWS_API_KEY = config.news_api_key

# Server
WEB_SERVER_HOST = config.web_server_host
WEB_SERVER_PORT = config.web_server_port
FRONTEND_ORIGIN = config.frontend_origin

# User
USER_NAME = config.user_name
