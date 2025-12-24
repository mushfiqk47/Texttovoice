"""
Configuration settings for Chatterbox TTS Backend.
Centralized settings with validation ranges using Pydantic Settings.
"""

import os
from pathlib import Path
from typing import List, Set, FrozenSet
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, computed_field

# =============================================================================
# SETTINGS CLASS
# =============================================================================

class Settings(BaseSettings):
    """
    Application configuration with strict validation.
    Reads from .env file automatically.
    """
    # Core App
    APP_TITLE: str = "Text To BOOK TTS API"
    APP_VERSION: str = "4.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Paths (Computed below, but can be overridden if needed)
    # We use computed fields for derived paths usually, but BaseSettings 
    # handles env vars mapping. Let's keep it simple.
    
    # TTS Parameters
    MAX_TEXT_LENGTH: int = Field(5000, ge=1)
    MAX_AUDIO_SIZE_MB: int = Field(100, ge=1)
    
    # Audio Formats
    ALLOWED_AUDIO_EXTENSIONS: FrozenSet[str] = frozenset({".wav", ".mp3", ".flac", ".ogg", ".m4a"})
    
    # Exaggeration (expressiveness)
    DEFAULT_EXAGGERATION: float = 1.0
    MIN_EXAGGERATION: float = 0.25
    MAX_EXAGGERATION: float = 2.0
    
    # CFG Weight (guidance)
    DEFAULT_CFG_WEIGHT: float = 0.5
    MIN_CFG_WEIGHT: float = 0.0
    MAX_CFG_WEIGHT: float = 1.0
    
    # GPU Settings
    GPU_ONLY: bool = False
    GPU_MEMORY_FRACTION: float = 0.9
    
    # Cleanup
    MAX_FILE_AGE_HOURS: int = 1
    CLEANUP_INTERVAL_MINUTES: int = 30
    
    # Security
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000", "http://127.0.0.1:8000"]
    RATE_LIMIT_PER_MINUTE: int = 10
    
    # Book Parsing
    ALLOWED_BOOK_EXTENSIONS: FrozenSet[str] = frozenset({".txt", ".epub", ".pdf"})
    
    # Optimization
    USE_TORCH_COMPILE: bool = True
    USE_AMP: bool = True
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore" # Ignore extra env vars
    )

    @property
    def BASE_DIR(self) -> Path:
        return Path(__file__).resolve().parent.parent

    @property
    def MODEL_DIR(self) -> Path:
        return self.BASE_DIR / "models" / "chatterbox-turbo"

    @property
    def OUTPUT_DIR(self) -> Path:
        return self.BASE_DIR / "output"

    @property
    def STATIC_DIR(self) -> Path:
        return self.BASE_DIR / "frontend"

    @property
    def VOICES_DIR(self) -> Path:
        return self.BASE_DIR / "voices"

# Instantiate global settings
settings = Settings()

# Export variables for backward compatibility with existing code
# (This allows us to refactor step-by-step or keep existing imports working)
APP_TITLE = settings.APP_TITLE
APP_VERSION = settings.APP_VERSION
HOST = settings.HOST
PORT = settings.PORT

MAX_TEXT_LENGTH = settings.MAX_TEXT_LENGTH
MAX_AUDIO_SIZE_MB = settings.MAX_AUDIO_SIZE_MB
ALLOWED_AUDIO_EXTENSIONS = settings.ALLOWED_AUDIO_EXTENSIONS

DEFAULT_EXAGGERATION = settings.DEFAULT_EXAGGERATION
MIN_EXAGGERATION = settings.MIN_EXAGGERATION
MAX_EXAGGERATION = settings.MAX_EXAGGERATION

DEFAULT_CFG_WEIGHT = settings.DEFAULT_CFG_WEIGHT
MIN_CFG_WEIGHT = settings.MIN_CFG_WEIGHT
MAX_CFG_WEIGHT = settings.MAX_CFG_WEIGHT

GPU_ONLY = settings.GPU_ONLY
GPU_MEMORY_FRACTION = settings.GPU_MEMORY_FRACTION

MAX_FILE_AGE_HOURS = settings.MAX_FILE_AGE_HOURS
CLEANUP_INTERVAL_MINUTES = settings.CLEANUP_INTERVAL_MINUTES

CORS_ORIGINS = settings.CORS_ORIGINS
RATE_LIMIT_PER_MINUTE = settings.RATE_LIMIT_PER_MINUTE

ALLOWED_BOOK_EXTENSIONS = settings.ALLOWED_BOOK_EXTENSIONS
USE_TORCH_COMPILE = settings.USE_TORCH_COMPILE
USE_AMP = settings.USE_AMP

# Path Exports
BASE_DIR = settings.BASE_DIR
MODEL_DIR = settings.MODEL_DIR
OUTPUT_DIR = settings.OUTPUT_DIR
STATIC_DIR = settings.STATIC_DIR
VOICES_DIR = settings.VOICES_DIR
