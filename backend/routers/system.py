from fastapi import APIRouter, HTTPException
import shutil
from ..config import APP_VERSION, OUTPUT_DIR
from ..services import tts_service
from pydantic import BaseModel
from typing import Optional
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    device: str
    version: str
    gpu_name: Optional[str] = None
    gpu_memory_mb: Optional[float] = None
    disk_free_gb: Optional[float] = None

class GPUInfoResponse(BaseModel):
    available: bool
    device: str
    device_count: int = 1
    memory_allocated_mb: float = 0
    memory_reserved_mb: float = 0
    memory_total_mb: float = 0
    cuda_version: str = "N/A"

@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """
    Health check endpoint with GPU status.
    Returns system health and GPU information.
    """
    try:
        model, device = tts_service.load_model()
        gpu_info = tts_service.get_gpu_info()
        
        # Check disk space
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

@router.get("/gpu-info", response_model=GPUInfoResponse)
def get_gpu_info() -> GPUInfoResponse:
    """
    Get detailed GPU information.
    Returns memory usage, CUDA version, and device details.
    """
    info = tts_service.get_gpu_info()
    return GPUInfoResponse(**info)

@router.post("/gpu-cleanup")
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
