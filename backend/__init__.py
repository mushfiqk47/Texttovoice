"""
Chatterbox TTS Backend Package.
"""

from .config import APP_TITLE, APP_VERSION
from .services import tts_service

__all__ = ["APP_TITLE", "APP_VERSION", "tts_service"]
