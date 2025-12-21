"""
Text To BOOK Application Orchestrator.
Unified entry point with GPU validation.
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging early
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("TextToBook")


def check_environment() -> bool:
    """
    Verify environment requirements.
    
    Returns:
        True if all checks pass
    """
    errors = []
    
    # Check Python version
    if sys.version_info < (3, 10):
        errors.append(f"Python 3.10+ required (found {sys.version})")
    
    # Check model directory
    model_dir = Path(__file__).parent / "models" / "chatterbox-turbo"
    if not model_dir.exists():
        errors.append(f"Model not found at {model_dir}")
    
    # Check GPU availability
    try:
        import torch
        if not torch.cuda.is_available():
            logger.warning("⚠️  CUDA GPU not available - Running in CPU mode (Performance will be slower)")
        else:
            logger.info(f"✅ GPU detected: {torch.cuda.get_device_name(0)}")
    except ImportError:
        errors.append("PyTorch not installed")
    
    if errors:
        for error in errors:
            logger.error(f"❌ {error}")
        return False
    
    logger.info("✅ Environment check passed")
    return True


def main() -> None:
    """Main application entry point."""
    print("\n" + "=" * 60)
    print("   📚 Text To BOOK - AI Audiobook Generator")
    print("=" * 60 + "\n")
    
    if not check_environment():
        print("\n❌ Environment check failed. See errors above.")
        sys.exit(1)
    
    # Import after environment check
    try:
        import uvicorn
        from backend.main import app
    except ImportError as e:
        logger.error(f"Failed to import backend: {e}")
        sys.exit(1)
    
    print("\n✅ Application initialized successfully")
    print("🚀 Server running at: http://localhost:8000")
    print("📋 API Docs: http://localhost:8000/docs")
    print("🖥️  GPU Info: http://localhost:8000/api/gpu-info")
    print("\nPress Ctrl+C to stop.\n")
    
    # Auto-open browser (optional)
    if os.environ.get("OPEN_BROWSER", "true").lower() == "true":
        import webbrowser
        from threading import Timer
        Timer(2.0, lambda: webbrowser.open("http://localhost:8000")).start()
    
    # Run server
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    main()
