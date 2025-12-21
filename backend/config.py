"""
Configuration settings for Chatterbox TTS Backend.
Centralized settings with validation ranges.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# PATH CONFIGURATION
# =============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "models" / "chatterbox-turbo"
OUTPUT_DIR = BASE_DIR / "output"
STATIC_DIR = BASE_DIR / "frontend"

# =============================================================================
# APPLICATION SETTINGS
# =============================================================================
APP_TITLE = "Text To BOOK TTS API"
APP_VERSION = "4.0.0"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# =============================================================================
# TTS PARAMETER SETTINGS
# =============================================================================
MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", "5000"))
MAX_AUDIO_SIZE_MB = int(os.getenv("MAX_AUDIO_SIZE_MB", "100"))

# Allowed audio extensions for reference audio
ALLOWED_AUDIO_EXTENSIONS = frozenset({".wav", ".mp3", ".flac", ".ogg", ".m4a"})

# Exaggeration (expressiveness) range
DEFAULT_EXAGGERATION = 1.0
MIN_EXAGGERATION = 0.25
MAX_EXAGGERATION = 2.0

# CFG Weight (guidance) range
DEFAULT_CFG_WEIGHT = 0.5
MIN_CFG_WEIGHT = 0.0
MAX_CFG_WEIGHT = 1.0

# =============================================================================
# GPU SETTINGS
# =============================================================================
# Force CUDA-only mode (will fail if no GPU)
GPU_ONLY = False

# Memory management
GPU_MEMORY_FRACTION = float(os.getenv("GPU_MEMORY_FRACTION", "0.9"))

# =============================================================================
# CLEANUP SETTINGS
# =============================================================================
MAX_FILE_AGE_HOURS = int(os.getenv("MAX_FILE_AGE_HOURS", "1"))
CLEANUP_INTERVAL_MINUTES = int(os.getenv("CLEANUP_INTERVAL_MINUTES", "30"))

# =============================================================================
# SECURITY SETTINGS
# =============================================================================
# CORS origins (comma-separated list or "*" for all)
# CORS origins
# Default to localhost for security, allow override via env
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000").split(",")

# Rate limiting (requests per minute per IP)
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))

# =============================================================================
# VOICE LIBRARY SETTINGS
# =============================================================================
VOICES_DIR = BASE_DIR / "voices"

# =============================================================================
# BOOK PARSING SETTINGS
# =============================================================================
ALLOWED_BOOK_EXTENSIONS = frozenset({".txt", ".epub", ".pdf"})

# =============================================================================
# GPU OPTIMIZATION FLAGS
# =============================================================================
# Use torch.compile for faster inference (PyTorch 2.0+)
USE_TORCH_COMPILE = os.getenv("USE_TORCH_COMPILE", "true").lower() == "true"

# Use Automatic Mixed Precision (FP16) for faster generation
USE_AMP = os.getenv("USE_AMP", "true").lower() == "true"
