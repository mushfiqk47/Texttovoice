from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks, Request
from fastapi.responses import FileResponse
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
from typing import Optional
import logging
import uuid
import shutil
import tempfile
import os
import torchaudio as ta
from pathlib import Path

from ..config import (
    OUTPUT_DIR, MAX_TEXT_LENGTH, DEFAULT_EXAGGERATION, MIN_EXAGGERATION, MAX_EXAGGERATION,
    DEFAULT_CFG_WEIGHT, MIN_CFG_WEIGHT, MAX_CFG_WEIGHT, ALLOWED_AUDIO_EXTENSIONS, MAX_AUDIO_SIZE_MB,
    RATE_LIMIT_PER_MINUTE
)
from ..utils import detect_language, cleanup_old_files
from ..services import tts_service

router = APIRouter()
logger = logging.getLogger(__name__)

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

from ..rate_limit import limiter

@router.post("/generate")
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute")
async def generate_speech(
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
    
    # Schedule background cleanup
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
            
            # Check file size (rough check via seek)
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
                pass
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_ref:
                shutil.copyfileobj(reference_audio.file, tmp_ref)
                ref_path = tmp_ref.name
        
        # Generate speech (ASYNCHRONOUS WRAPPER)
        # This prevents blocking the main event loop while the GPU works
        try:
             wav, sr = await run_in_threadpool(
                tts_service.generate,
                text, 
                ref_path, 
                exaggeration, 
                cfg_weight
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                 raise HTTPException(status_code=503, detail="GPU out of memory. Try shorter text or clearing cache.")
            raise HTTPException(status_code=503, detail=f"Generation failed: {str(e)}")

        # Save output
        filename = f"{uuid.uuid4()}.wav"
        output_path = OUTPUT_DIR / filename
        
        # Saving file is I/O bound, can also be wrapped or just done directly (fast for wav)
        await run_in_threadpool(ta.save, str(output_path), wav, sr)
        
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
