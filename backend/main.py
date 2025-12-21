"""
FastAPI Main Application Module.
Defines routes, API structure, and GPU endpoints.
"""

import uuid
import logging
import tempfile
import os
import shutil
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import torchaudio as ta
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .config import (
    APP_TITLE, APP_VERSION, OUTPUT_DIR, STATIC_DIR, VOICES_DIR,
    MAX_TEXT_LENGTH, MAX_AUDIO_SIZE_MB, ALLOWED_AUDIO_EXTENSIONS, ALLOWED_BOOK_EXTENSIONS,
    MIN_EXAGGERATION, MAX_EXAGGERATION, MIN_CFG_WEIGHT, MAX_CFG_WEIGHT,
    DEFAULT_EXAGGERATION, DEFAULT_CFG_WEIGHT, CORS_ORIGINS,
    RATE_LIMIT_PER_MINUTE
)
from .utils import detect_language, cleanup_old_files
from .services import tts_service
from .parsers import parse_book

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)

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
        tts_service.load_model()
        gpu_info = tts_service.get_gpu_info()
        logger.info(f"GPU: {gpu_info.get('device', 'N/A')}")
        logger.info(f"CUDA Version: {gpu_info.get('cuda_version', 'N/A')}")
        logger.info(f"VRAM: {gpu_info.get('memory_total_mb', 0):.0f}MB")
    except Exception as e:
        logger.error(f"Model pre-loading failed: {e}")
        # Don't exit - allow health check to report unhealthy
    
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

# Rate Limiter Setup
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
# RESPONSE MODELS
# =============================================================================
class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    model_loaded: bool
    device: str
    version: str
    gpu_name: Optional[str] = None
    gpu_memory_mb: Optional[float] = None
    disk_free_gb: Optional[float] = None


class GPUInfoResponse(BaseModel):
    """Detailed GPU information response."""
    available: bool
    device: str
    device_count: int = 1
    memory_allocated_mb: float = 0
    memory_reserved_mb: float = 0
    memory_total_mb: float = 0
    cuda_version: str = "N/A"


class GenerateRequest(BaseModel):
    """Generation request model for validation."""
    text: str = Field(..., min_length=1, max_length=MAX_TEXT_LENGTH)
    exaggeration: float = Field(
        default=DEFAULT_EXAGGERATION, 
        ge=MIN_EXAGGERATION, 
        le=MAX_EXAGGERATION
    )
    cfg_weight: float = Field(
        default=DEFAULT_CFG_WEIGHT, 
        ge=MIN_CFG_WEIGHT, 
        le=MAX_CFG_WEIGHT
    )

# =============================================================================
# API ENDPOINTS
# =============================================================================
@app.get("/api/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """
    Health check endpoint with GPU status.
    Returns system health and GPU information.
    """
    try:
        model, device = tts_service.load_model()
        gpu_info = tts_service.get_gpu_info()
        
        # Check disk space
        import shutil
        total, used, free = shutil.disk_usage(OUTPUT_DIR)
        disk_free_gb = free / (1024**3)

        return HealthResponse(
            status="healthy",
            model_loaded=model is not None,
            device=device,
            version=APP_VERSION,
            gpu_name=gpu_info.get("device"),
            gpu_memory_mb=gpu_info.get("memory_total_mb"),
            disk_free_gb=round(disk_free_gb, 2)
        )
    except Exception as e:
        logger.warning(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            model_loaded=False,
            device="unavailable",
            version=APP_VERSION
        )


@app.get("/api/gpu-info", response_model=GPUInfoResponse)
def get_gpu_info() -> GPUInfoResponse:
    """
    Get detailed GPU information.
    Returns memory usage, CUDA version, and device details.
    """
    info = tts_service.get_gpu_info()
    return GPUInfoResponse(**info)


@app.post("/api/gpu-cleanup")
async def gpu_cleanup():
    """Clear GPU cache and memory."""
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        return {"status": "success", "message": "GPU cache cleared"}
    except Exception as e:
        logger.error(f"GPU cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate")
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute")
def generate_speech(
    request: Request,
    background_tasks: BackgroundTasks,
    text: str = Form(..., description="Text to synthesize"),
    exaggeration: float = Form(
        default=DEFAULT_EXAGGERATION, 
        ge=MIN_EXAGGERATION, 
        le=MAX_EXAGGERATION,
        description="Expression level (0.25-2.0)"
    ),
    cfg_weight: float = Form(
        default=DEFAULT_CFG_WEIGHT, 
        ge=MIN_CFG_WEIGHT, 
        le=MAX_CFG_WEIGHT,
        description="Guidance weight (0.0-1.0)"
    ),
    reference_audio: Optional[UploadFile] = File(
        default=None, 
        description="Optional reference audio for voice cloning"
    )
) -> FileResponse:
    """
    Generate speech from text using GPU-accelerated TTS.
    
    - **text**: Text to convert to speech (max 5000 characters)
    - **exaggeration**: Expression level from flat (0.25) to dynamic (2.0)
    - **cfg_weight**: Guidance from creative (0.0) to precise (1.0)
    - **reference_audio**: Optional audio file for voice cloning
    """
    # Input validation
    text = text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    if len(text) > MAX_TEXT_LENGTH:
        raise HTTPException(
            status_code=400, 
            detail=f"Text exceeds maximum length of {MAX_TEXT_LENGTH} characters"
        )
    
    # Language detection (Sync but fast after lazy load)
    try:
        lang_code, lang_conf = detect_language(text)
    except Exception as e:
        logger.warning(f"Language detection failure: {e}")
        lang_code, lang_conf = "unknown", 0.0
    
    # Schedule background cleanup (Now async compatible)
    background_tasks.add_task(cleanup_old_files)
    
    # Handle reference audio
    ref_path: Optional[str] = None
    
    try:
        if reference_audio and reference_audio.filename:
            ext = Path(reference_audio.filename).suffix.lower()
            if ext not in ALLOWED_AUDIO_EXTENSIONS:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid audio format. Allowed: {', '.join(ALLOWED_AUDIO_EXTENSIONS)}"
                )
            
            # Check file size
            # Use seek/tell only if supported (workaround for some spooled files)
            try:
                reference_audio.file.seek(0, 2)
                size_mb = reference_audio.file.tell() / 1024 / 1024
                reference_audio.file.seek(0)
                
                if size_mb > MAX_AUDIO_SIZE_MB:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Audio file too large. Maximum: {MAX_AUDIO_SIZE_MB}MB"
                    )
            except (AttributeError, ValueError):
                # Fallback for streams that don't support seek
                pass
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_ref:
                shutil.copyfileobj(reference_audio.file, tmp_ref)
                ref_path = tmp_ref.name
        
        # Generate speech (GPU)
        # This is a synchronous blocking call on GPU, but runs in threadpool if we wanted 
        # (currently services.py is sync but fast enough for single user)
        # For multi-user, we'd want to wrap this in run_in_executor too, 
        # but PyTorch + CUDA in sub-threads can be tricky.
        # Keeping main thread for now as it's a local tool.
        wav, sr = tts_service.generate(text, ref_path, exaggeration, cfg_weight)
        
        # Save output
        filename = f"{uuid.uuid4()}.wav"
        output_path = OUTPUT_DIR / filename
        ta.save(str(output_path), wav, sr)
        
        logger.info(f"Generated: {filename} ({len(text)} chars) | Lang: {lang_code}")
        
        return FileResponse(
            path=str(output_path),
            media_type="audio/wav",
            filename=filename,
            headers={
                "X-Detected-Language": lang_code,
                "X-Language-Confidence": str(round(lang_conf, 2)),
                "X-Text-Length": str(len(text)),
                "X-Generated-Filename": filename
            }
        )
    
    except HTTPException:
        raise
    except RuntimeError as e:
        # GPU errors
        logger.error(f"GPU error during generation: {e}")
        if "out of memory" in str(e).lower():
             raise HTTPException(status_code=503, detail="GPU out of memory. Try shorter text or clearing cache.")
        raise HTTPException(status_code=503, detail=f"GPU processing failed: {str(e)}")
    except Exception as e:
        logger.error(f"Generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal generation failure")
    finally:
        # Cleanup temp reference file
        if ref_path and os.path.exists(ref_path):
            try:
                os.unlink(ref_path)
            except OSError as e:
                logger.warning(f"Failed to cleanup temp file: {e}")


@app.delete("/api/audio/{filename}")
def delete_audio(filename: str) -> dict:
    """
    Delete a generated audio file from disk.
    """
    # Sanitize filename to prevent directory traversal
    safe_filename = Path(filename).name
    file_path = OUTPUT_DIR / safe_filename
    
    if file_path.exists() and file_path.is_file():
        try:
            file_path.unlink()
            logger.info(f"Deleted audio file: {safe_filename}")
            return {"status": "success", "message": f"Deleted {safe_filename}"}
        except Exception as e:
            logger.error(f"Failed to delete file {safe_filename}: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete file")
    else:
        raise HTTPException(status_code=404, detail="File not found")


@app.post("/api/clear-gpu-cache")
def clear_gpu_cache() -> dict:
    """
    Manually clear GPU memory cache.
    Useful if memory is fragmented after many generations.
    """
    tts_service._cleanup_gpu_memory()
    info = tts_service.get_gpu_info()
    return {
        "status": "cleared",
        "memory_allocated_mb": info.get("memory_allocated_mb", 0),
        "memory_reserved_mb": info.get("memory_reserved_mb", 0)
    }


# =============================================================================
# BOOK PARSING ENDPOINT
# =============================================================================
@app.post("/api/parse-book")
async def parse_book_file(
    file: UploadFile = File(..., description="Book file (.txt, .epub, .pdf)")
) -> dict:
    """
    Parse a book file and extract text content.
    Supports TXT, EPUB, and PDF formats.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_BOOK_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format. Allowed: {', '.join(ALLOWED_BOOK_EXTENSIONS)}"
        )
    
    try:
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = Path(tmp.name)
        
        # Parse content
        content = parse_book(tmp_path)
        
        # Cleanup
        tmp_path.unlink()
        
        return {
            "status": "success",
            "filename": file.filename,
            "content": content,
            "length": len(content)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Book parsing error: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse book")


# =============================================================================
# VOICE LIBRARY ENDPOINTS
# =============================================================================
@app.get("/api/voices")
def list_voices() -> dict:
    """List all saved voice presets."""
    VOICES_DIR.mkdir(exist_ok=True)
    
    voices = []
    for file in VOICES_DIR.glob("*.wav"):
        voices.append({
            "name": file.stem,
            "filename": file.name,
            "size_kb": round(file.stat().st_size / 1024, 1)
        })
    
    return {"voices": voices}


@app.post("/api/voices")
async def save_voice(
    name: str = Form(..., description="Voice preset name"),
    audio: UploadFile = File(..., description="Reference audio file")
) -> dict:
    """Save a new voice preset."""
    VOICES_DIR.mkdir(exist_ok=True)
    
    # Sanitize name
    safe_name = "".join(c for c in name if c.isalnum() or c in "-_").strip()
    if not safe_name:
        raise HTTPException(status_code=400, detail="Invalid voice name")
    
    # Check extension
    ext = Path(audio.filename).suffix.lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid audio format")
    
    # Save file as .wav (even if it's another format, we keep original for now)
    voice_path = VOICES_DIR / f"{safe_name}.wav"
    
    try:
        with open(voice_path, "wb") as f:
            shutil.copyfileobj(audio.file, f)
        
        return {"status": "success", "name": safe_name, "filename": voice_path.name}
    except Exception as e:
        logger.error(f"Failed to save voice: {e}")
        raise HTTPException(status_code=500, detail="Failed to save voice")


@app.delete("/api/voices/{name}")
def delete_voice(name: str) -> dict:
    """Delete a saved voice preset."""
    safe_name = Path(name).stem
    voice_path = VOICES_DIR / f"{safe_name}.wav"
    
    if voice_path.exists() and voice_path.is_file():
        try:
            voice_path.unlink()
            return {"status": "success", "message": f"Deleted voice: {safe_name}"}
        except Exception as e:
            logger.error(f"Failed to delete voice {safe_name}: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete voice")
    else:
        raise HTTPException(status_code=404, detail="Voice not found")


# =============================================================================
# MP3 CONVERSION ENDPOINT
# =============================================================================
@app.get("/api/audio/{filename}/mp3")
def convert_to_mp3(filename: str) -> FileResponse:
    """
    Convert a WAV file to MP3 format on-the-fly.
    Returns the MP3 file for download.
    """
    safe_filename = Path(filename).name
    wav_path = OUTPUT_DIR / safe_filename
    
    if not wav_path.exists() or not wav_path.is_file():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    try:
        from pydub import AudioSegment
        
        # Convert WAV to MP3
        mp3_filename = wav_path.stem + ".mp3"
        mp3_path = OUTPUT_DIR / mp3_filename
        
        audio = AudioSegment.from_wav(str(wav_path))
        audio.export(str(mp3_path), format="mp3", bitrate="192k")
        
        return FileResponse(
            path=str(mp3_path),
            media_type="audio/mpeg",
            filename=mp3_filename
        )
    except ImportError:
        raise HTTPException(status_code=500, detail="MP3 conversion not available (pydub missing)")
    except Exception as e:
        logger.error(f"MP3 conversion failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to convert to MP3")


# Static Files (Must be last)
if OUTPUT_DIR.exists():
    app.mount("/audio", StaticFiles(directory=str(OUTPUT_DIR)), name="audio")
    logger.info(f"Serving audio from {OUTPUT_DIR}")

# Create and mount voices directory for voice presets
VOICES_DIR.mkdir(exist_ok=True)
app.mount("/voices", StaticFiles(directory=str(VOICES_DIR)), name="voices")
logger.info(f"Serving voices from {VOICES_DIR}")

if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="frontend")
