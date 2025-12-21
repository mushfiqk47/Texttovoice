"""
Utility functions for Text To BOOK Backend.
Includes language detection and file cleanup.
"""

import time
import logging
from pathlib import Path
from typing import Tuple

from .config import OUTPUT_DIR, MAX_FILE_AGE_HOURS

logger = logging.getLogger(__name__)

# =============================================================================
# LANGUAGE DETECTION
# =============================================================================
# Lazy-load langdetect to avoid import overhead if not used
_langdetect_available: bool = None
_detect_langs = None


def _init_langdetect() -> bool:
    """Initialize langdetect module lazily."""
    global _langdetect_available, _detect_langs
    
    if _langdetect_available is not None:
        return _langdetect_available
    
    try:
        from langdetect import detect_langs as _dl
        _detect_langs = _dl
        _langdetect_available = True
    except ImportError:
        _langdetect_available = False
        logger.warning("langdetect not installed - language detection disabled")
    
    return _langdetect_available


def detect_language(text: str) -> Tuple[str, float]:
    """
    Detect the primary language of the given text.
    
    Args:
        text: Text to analyze
        
    Returns:
        Tuple of (language_code, confidence_score)
        Returns ("unknown", 0.0) if detection fails
    """
    # Validate input
    if not text or len(text.strip()) < 10:
        return "unknown", 0.0
    
    # Initialize langdetect lazily
    if not _init_langdetect():
        return "unknown", 0.0
    
    try:
        # Get language probabilities
        langs = _detect_langs(text)
        if not langs:
            return "unknown", 0.0
        
        # Return primary language
        primary = langs[0]
        return primary.lang, round(primary.prob, 4)
        
    except Exception as e:
        # Catch all langdetect exceptions
        logger.debug(f"Language detection failed: {e}")
        return "unknown", 0.0


# =============================================================================
# FILE CLEANUP
# =============================================================================
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Executor for file operations
file_executor = ThreadPoolExecutor(max_workers=1)

async def cleanup_old_files(directory: Path = None, max_age_hours: int = None) -> int:
    """
    Remove generated audio files older than specified age.
    Runs in a separate thread to avoid blocking the event loop.
    
    Args:
        directory: Directory to clean (default: OUTPUT_DIR)
        max_age_hours: Max file age in hours (default: from config)
        
    Returns:
        Number of files deleted
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        file_executor, 
        _cleanup_old_files_sync, 
        directory, 
        max_age_hours
    )

def _cleanup_old_files_sync(directory: Path = None, max_age_hours: int = None) -> int:
    """Synchronous implementation of file cleanup."""
    target_dir = directory or OUTPUT_DIR
    max_age = max_age_hours if max_age_hours is not None else MAX_FILE_AGE_HOURS
    
    if not target_dir.exists():
        return 0
    
    current_time = time.time()
    max_age_seconds = max_age * 3600
    deleted_count = 0
    
    try:
        for file in target_dir.glob("*.wav"):
            try:
                # Basic check to avoid deleting files currently being written (too new)
                # e.g. < 5 seconds old
                if current_time - file.stat().st_mtime < 5:
                    continue

                file_age = current_time - file.stat().st_mtime
                if file_age > max_age_seconds:
                    file.unlink()
                    deleted_count += 1
            except OSError as e:
                logger.warning(f"Failed to delete {file.name}: {e}")
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old audio files")
            
    except Exception as e:
        logger.error(f"Error during file cleanup: {e}")
    
    return deleted_count


def get_output_stats() -> dict:
    """
    Get statistics about the output directory.
    
    Returns:
        Dictionary with file count, total size, etc.
    """
    if not OUTPUT_DIR.exists():
        return {"file_count": 0, "total_size_mb": 0}
    
    files = list(OUTPUT_DIR.glob("*.wav"))
    total_size = sum(f.stat().st_size for f in files)
    
    return {
        "file_count": len(files),
        "total_size_mb": round(total_size / 1024 / 1024, 2)
    }
