"""
TTS Service logic for Chatterbox Backend.
Handles model loading, audio generation, and GPU memory management.
"""

import os
import gc
import logging
from typing import Tuple, Optional, Dict, Any

import torch
import torchaudio as ta

import re
from chatterbox.tts_turbo import ChatterboxTurboTTS
from .config import (
    MODEL_DIR, 
    DEFAULT_EXAGGERATION, 
    DEFAULT_CFG_WEIGHT,
    MIN_EXAGGERATION,
    MAX_EXAGGERATION,
    MIN_CFG_WEIGHT,
    MAX_CFG_WEIGHT,
    USE_AMP
)

logger = logging.getLogger(__name__)


class TTSService:
    """
    Singleton TTS service with GPU-only execution.
    Manages model lifecycle and GPU memory.
    """
    _instance: Optional["TTSService"] = None
    
    def __new__(cls) -> "TTSService":
        if cls._instance is None:
            cls._instance = super(TTSService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        if self._initialized:
            return
        self.model: Optional[ChatterboxTurboTTS] = None
        self.device: str = "cpu"
        self._initialized = True
    
    def load_model(self) -> Tuple[ChatterboxTurboTTS, str]:
        """
        Load the model if not already loaded.
        Allows CPU execution if CUDA is not available.
        
        Returns:
            Tuple of (model, device_string)
        """
        if self.model is not None:
            return self.model, self.device
        
        # Check for CUDA but allow CPU fallback
        if torch.cuda.is_available():
            self.device = "cuda"
            logger.info(f"✅ CUDA GPU detected: {torch.cuda.get_device_name(0)}")
            logger.info(f"   CUDA Version: {torch.version.cuda}")
            logger.info(f"   PyTorch Version: {torch.__version__}")
        else:
            self.device = "cpu"
            logger.warning("⚠️  CUDA GPU not found! Running in CPU mode (slower).")
            logger.info(f"   PyTorch Version: {torch.__version__}")
            logger.info("   (Running in CPU mode)")
        
        # Verify model directory
        if not MODEL_DIR.exists():
             raise RuntimeError(
                f"Model directory not found: {MODEL_DIR}. "
                "The project requires model files to be present in the codebase."
            )
        
        logger.info(f"Loading Chatterbox-Turbo model on {self.device}...")
        
        try:
            self.model = ChatterboxTurboTTS.from_local(str(MODEL_DIR), self.device)
            logger.info("✅ Model loaded successfully!")
            
            if self.device == "cuda":
                # Enable Access to CuDNN Benchmark for consistent input sizes
                torch.backends.cudnn.benchmark = True
                
                # Use torch.compile for faster inference (PyTorch 2+)
                from .config import USE_TORCH_COMPILE
                if USE_TORCH_COMPILE:
                     try:
                        logger.info("🚀 Compiling model with torch.compile...")
                        self.model.model = torch.compile(self.model.model, mode="reduce-overhead")
                     except Exception as e:
                        logger.warning(f"torch.compile failed, falling back to eager mode: {e}")
                        
            self._log_gpu_memory()
        except Exception as e:
            logger.critical(f"FATAL: Failed to load Chatterbox model: {e}", exc_info=True)
            # We raise so the caller knows it failed, effectively 'crashing' the request if happening during generation
            raise
        
        return self.model, self.device

    def generate(
        self, 
        text: str, 
        audio_prompt_path: Optional[str] = None, 
        exaggeration: float = DEFAULT_EXAGGERATION, 
        cfg_weight: float = DEFAULT_CFG_WEIGHT
    ) -> Tuple[torch.Tensor, int]:
        """
        Generate audio from text with GPU memory management.
        
        Args:
            text: Text to synthesize
            audio_prompt_path: Optional path to reference audio
            exaggeration: Expression level (0.25-2.0)
            cfg_weight: Classifier-free guidance weight (0.0-1.0)
            
        Returns:
            Tuple of (waveform_tensor, sample_rate)
        """
        model, device = self.load_model()
        
        # Clamp parameters to valid ranges
        exaggeration = max(MIN_EXAGGERATION, min(MAX_EXAGGERATION, exaggeration))
        cfg_weight = max(MIN_CFG_WEIGHT, min(MAX_CFG_WEIGHT, cfg_weight))
        
        try:
            # Split text into chunks (sentences/segments) to prevent noise artifacts
            chunks = self._split_text(text)
            logger.info(f"Generating {len(chunks)} chunks")
            
            # Extract speaker embeddings ONCE for the entire request
            if audio_prompt_path:
                try:
                    logger.info(f"Extracting speaker embeddings from: {audio_prompt_path}")
                    model.prepare_conditionals(audio_prompt_path)
                except AssertionError as e:
                    logger.warning(f"Voice cloning failed: {e}")
                    # If cloning fails (e.g. too short), we might want to fail or use default
                    # For now, let's raise a clearer error
                    raise ValueError(str(e))
                except Exception as e:
                    logger.error(f"Error preparing voice clone: {e}")
                    raise RuntimeError(f"Cloning failed: {e}")
            
            waveforms = []
            
            # Determine if we should use AMP (only if CUDA and configured)
            use_amp = USE_AMP and (self.device == "cuda")
            
            for i, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue
                
                logger.debug(f"Generating chunk {i+1}/{len(chunks)}")
                
                # Calling model.generate WITHOUT audio_prompt_path uses the stored conditionals
                # This is much faster as it avoids re-extracting embeddings for every chunk
                if use_amp:
                    with torch.cuda.amp.autocast():
                        chunk_wav = model.generate(
                            chunk,
                            exaggeration=exaggeration,
                            cfg_weight=cfg_weight
                        )
                else:
                    # CPU / No AMP execution
                    chunk_wav = model.generate(
                        chunk,
                        exaggeration=exaggeration,
                        cfg_weight=cfg_weight
                    )
                
                waveforms.append(chunk_wav)
            
            if not waveforms:
                return torch.zeros((1, 1)), model.sr
            
            # Concatenate chunks
            full_wav = torch.cat(waveforms, dim=-1)
            
            # Peak Normalization to -1dB (approx 0.89) to prevent clipping noise
            full_wav = self._normalize_audio(full_wav)
            
            return full_wav, model.sr
            
        finally:
            # GPU memory cleanup after generation
            self._cleanup_gpu_memory()
            # Important: Reset model conditionals if we were using a custom one
            # to avoid the next request using the previous speaker by mistake
            # (Since model is a singleton)
            # However, ChatterboxTurboTTS doesn't have an easy "reset_conds"
            # We can re-load default or just be aware of this.

        return chunks if chunks else [text]

    def _split_text(self, text: str, max_chunk_len: int = 400) -> list:
        """
        Split text into natural chunks (sentences) for better TTS quality.
        Increased default chunk length to reduce overhead.
        """
        # Simple but effective splitting by sentence terminators
        # We use a lookbehind to keep the delimiter with the sentence
        
        # 1. Clean up text
        text = text.strip()
        if not text:
            return []
            
        # 2. Split by sentence endings (. ! ?)
        # This regex splits by (.!?) but keeps the delimiter attached to the PREVIOUS chunk
        # It's a bit complex, so we use the standard re.split with capture groups
        parts = re.split(r'([.!?]+)', text)
        
        # 3. Re-combine parts to form complete sentences
        sentences = []
        for i in range(0, len(parts) - 1, 2):
            sentences.append(parts[i] + parts[i+1])
        if len(parts) % 2 == 1 and parts[-1]:
            sentences.append(parts[-1])
            
        # 4. Combine sentences into optimal chunks
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # If a single sentence is too long, we might need to force split it (not implemented here for simplicity)
            # but we check if adding it exceeds the limit
            if len(current_chunk) + len(sentence) + 1 < max_chunk_len:
                current_chunk += (" " + sentence) if current_chunk else sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks

    def _normalize_audio(self, wav: torch.Tensor) -> torch.Tensor:
        """
        Apply peak normalization to prevent digital clipping.
        """
        abs_max = torch.max(torch.abs(wav))
        if abs_max > 0:
            # Normalize to 0.9 (approx -1dB) if it exceeds threshold
            # or always normalize for consistent volume
            wav = wav * (0.9 / abs_max)
        return wav

    def get_gpu_info(self) -> Dict[str, Any]:
        """
        Get detailed GPU information.
        
        Returns:
            Dictionary with GPU stats
        """
        if not torch.cuda.is_available():
            return {
                "available": False,
                "device": "N/A",
                "memory_allocated_mb": 0,
                "memory_reserved_mb": 0,
                "memory_total_mb": 0
            }
        
        return {
            "available": True,
            "device": torch.cuda.get_device_name(0),
            "device_count": torch.cuda.device_count(),
            "memory_allocated_mb": round(torch.cuda.memory_allocated(0) / 1024 / 1024, 2),
            "memory_reserved_mb": round(torch.cuda.memory_reserved(0) / 1024 / 1024, 2),
            "memory_total_mb": round(torch.cuda.get_device_properties(0).total_memory / 1024 / 1024, 2),
            "cuda_version": torch.version.cuda or "Unknown"
        }
    
    def _cleanup_gpu_memory(self) -> None:
        """Clear GPU memory cache after operations."""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            gc.collect()
            logger.debug("GPU memory cache cleared")
    
    def _log_gpu_memory(self) -> None:
        """Log current GPU memory usage."""
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated(0) / 1024 / 1024
            reserved = torch.cuda.memory_reserved(0) / 1024 / 1024
            logger.info(f"GPU Memory - Allocated: {allocated:.2f}MB, Reserved: {reserved:.2f}MB")

    def unload_model(self) -> None:
        """Unload model and free GPU memory."""
        if self.model is not None:
            del self.model
            self.model = None
            self._cleanup_gpu_memory()
            logger.info("Model unloaded and GPU memory freed")


# Singleton instance
tts_service = TTSService()
