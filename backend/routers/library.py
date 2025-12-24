from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pathlib import Path
import shutil
import tempfile
import logging
import os
from ..config import (
    OUTPUT_DIR, VOICES_DIR, ALLOWED_AUDIO_EXTENSIONS, ALLOWED_BOOK_EXTENSIONS
)
from ..parsers import parse_book

router = APIRouter()
logger = logging.getLogger(__name__)

# =============================================================================
# VOICE LIBRARY ENDPOINTS
# =============================================================================
@router.get("/voices")
def list_voices() -> dict:
    """List all saved voice presets."""
    VOICES_DIR.mkdir(exist_ok=True)
    
    voices = []
    # Scan for all allowed extensions
    for ext in ALLOWED_AUDIO_EXTENSIONS:
        # glob is case sensitive on some OS, but extensions is set lower
        for file in VOICES_DIR.glob(f"*{ext}"):
             voices.append({
                "name": file.stem,
                "filename": file.name,
                "size_kb": round(file.stat().st_size / 1024, 1)
            })
    
    # Sort by name
    voices.sort(key=lambda x: x["name"])
    
    return {"voices": voices}


@router.post("/voices")
async def save_voice(
    name: str = Form(..., description="Voice preset name"),
    audio: UploadFile = File(..., description="Reference audio file")
) -> dict:
    """Save a new voice preset."""
    VOICES_DIR.mkdir(exist_ok=True)
    
    # Sanitize name - Strict Alphanumeric + Hyphen/Underscore
    safe_name = "".join(c for c in name if c.isalnum() or c in "-_").strip()
    if not safe_name:
        raise HTTPException(status_code=400, detail="Invalid voice name")
    
    # Check extension
    if not audio.filename:
        raise HTTPException(status_code=400, detail="Invalid file")
        
    ext = Path(audio.filename).suffix.lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid audio format")
    
    # Save file with original extension
    voice_path = VOICES_DIR / f"{safe_name}{ext}"
    
    try:
        with open(voice_path, "wb") as f:
            shutil.copyfileobj(audio.file, f)
        
        return {"status": "success", "name": safe_name, "filename": voice_path.name}
    except Exception as e:
        logger.error(f"Failed to save voice: {e}")
        raise HTTPException(status_code=500, detail="Failed to save voice")


@router.delete("/voices/{name}")
def delete_voice(name: str) -> dict:
    """Delete a saved voice preset."""
    # Security: Use os.path.basename to prevent traversal
    safe_name = Path(os.path.basename(name)).stem
    
    # Find the file (we don't know the extension)
    voice_path = None
    for ext in ALLOWED_AUDIO_EXTENSIONS:
        check_path = VOICES_DIR / f"{safe_name}{ext}"
        if check_path.exists():
            voice_path = check_path
            break
            
    if voice_path and voice_path.is_file():
        try:
            voice_path.unlink()
            return {"status": "success", "message": f"Deleted voice: {safe_name}"}
        except Exception as e:
            logger.error(f"Failed to delete voice {safe_name}: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete voice")
    else:
        raise HTTPException(status_code=404, detail="Voice not found")

# =============================================================================
# AUDIO FILE MANAGEMENT
# =============================================================================
@router.delete("/audio/{filename}")
def delete_audio(filename: str) -> dict:
    """
    Delete a generated audio file from disk.
    """
    # Sanitize filename to prevent directory traversal
    safe_filename = os.path.basename(filename)
    file_path = OUTPUT_DIR / safe_filename
    
    # Strict check that we are staying within OUTPUT_DIR
    if file_path.parent != OUTPUT_DIR:
         raise HTTPException(status_code=403, detail="Access denied")

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


@router.get("/audio/{filename}/mp3")
def convert_to_mp3(filename: str) -> FileResponse:
    """
    Convert a WAV file to MP3 format on-the-fly.
    Returns the MP3 file for download.
    """
    safe_filename = os.path.basename(filename)
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

# =============================================================================
# BOOK PARSING ENDPOINT
# =============================================================================
@router.post("/parse-book")
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
        # Run in threadpool to prevent blocking the event loop during heavy parsing (PDFs)
        from fastapi.concurrency import run_in_threadpool
        content = await run_in_threadpool(parse_book, tmp_path)
        
        # Cleanup
        tmp_path.unlink()
        
        return {
            "status": "success",
            "filename": file.filename,
            "content": content,
            "length": len(content)
        }
    except ValueError as e:
        if 'tmp_path' in locals() and tmp_path.exists():
             tmp_path.unlink()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        if 'tmp_path' in locals() and tmp_path.exists():
             tmp_path.unlink()
        logger.error(f"Book parsing error: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse book")
