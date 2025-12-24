"""
FastAPI Main Application Module.
Refactored to use modular routers.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .config import (
    APP_TITLE, APP_VERSION, OUTPUT_DIR, STATIC_DIR, VOICES_DIR, CORS_ORIGINS
)
from .utils import cleanup_old_files
from .services import tts_service
from .routers import system, tts, library
from .main_utils import limiter  # We need to move limiter to a shared utils or keep in main for simplicity

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# =============================================================================
# APPLICATION LIFECYCLE
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    # Startup
    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
    logger.info("=" * 50)
    logger.info("Text To BOOK Backend starting...")
    logger.info("=" * 50)
    
    # Pre-load model and log GPU info
    try:
        # We can run this in threadpool if it blocks too much, but usually acceptable for startup
        tts_service.load_model()
        gpu_info = tts_service.get_gpu_info()
        logger.info(f"GPU: {gpu_info.get('device', 'N/A')}")
        logger.info(f"CUDA Version: {gpu_info.get('cuda_version', 'N/A')}")
    except Exception as e:
        logger.error(f"Model pre-loading failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    cleanup_old_files()
    tts_service.unload_model()

# =============================================================================
# FASTAPI APPLICATION
# =============================================================================
app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description="AI-powered Text-to-Speech with GPU acceleration",
    lifespan=lifespan
)

# Rate Limiter
# Ideally, limiter should be in a separate file to avoid circular imports if routers need it
# For now, we attach it here. Routers that need it can import it from a common place.
# Let's create 'backend/main_utils.py' for the limiter to be clean.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# =============================================================================
# ROUTERS
# =============================================================================
app.include_router(system.router, prefix="/api", tags=["System"])
app.include_router(tts.router, prefix="/api", tags=["TTS"])
app.include_router(library.router, prefix="/api", tags=["Library"])

# =============================================================================
# STATIC FILES
# =============================================================================
if OUTPUT_DIR.exists():
    app.mount("/audio", StaticFiles(directory=str(OUTPUT_DIR)), name="audio")

VOICES_DIR.mkdir(exist_ok=True)
app.mount("/voices", StaticFiles(directory=str(VOICES_DIR)), name="voices")

if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="frontend")
