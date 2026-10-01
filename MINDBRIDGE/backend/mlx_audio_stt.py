"""
MLX-Audio STT Adapter (Blaizzy Architecture)
High-performance Speech-to-Text integration powered by mlx-audio / mlx-whisper.
Designed for Apple Silicon M-series chips with graceful cross-platform fallback.
Repository: https://github.com/Blaizzy/mlx-audio
"""

import os
import io
import sys
import logging
from typing import Optional, Dict, Any, Union

logger = logging.getLogger("mindbridge.mlx_audio_stt")

# Check if mlx-audio or mlx-whisper is available
MLX_AVAILABLE = False
_stt_backend = None

try:
    import mlx_audio.stt as mlx_stt  # type: ignore[import-not-found]
    MLX_AVAILABLE = True
    _stt_backend = "mlx_audio"
except ImportError:
    try:
        import mlx_whisper  # type: ignore[import-not-found]
        MLX_AVAILABLE = True
        _stt_backend = "mlx_whisper"
    except ImportError:
        MLX_AVAILABLE = False
        _stt_backend = None


class MLXAudioTranscriber:
    """
    Adapter for mlx-audio / mlx-whisper STT engine.
    Supports transcribing raw audio bytes (WAV, PCM, WebM, etc.) or audio files.
    """
    def __init__(self, model_name: str = "mlx-community/whisper-large-v3-turbo"):
        self.model_name = model_name
        self.model = None
        self._is_loaded = False
        self.backend = _stt_backend

    def is_available(self) -> bool:
        """Returns True if mlx-audio or mlx-whisper is available on this environment."""
        return MLX_AVAILABLE

    def _ensure_loaded(self):
        """Loads model into memory on first transcribe call."""
        if not MLX_AVAILABLE or self._is_loaded:
            return
        try:
            if self.backend == "mlx_audio":
                import mlx_audio.stt as mlx_stt  # type: ignore[import-not-found]
                self.model = mlx_stt.load_model(self.model_name)
            self._is_loaded = True
            logger.info(f"[MLX-Audio] Model '{self.model_name}' loaded successfully via {self.backend}.")
        except Exception as e:
            logger.warning(f"[MLX-Audio] Failed to load model '{self.model_name}': {e}")
            self._is_loaded = False

    def transcribe_audio_bytes(
        self,
        audio_bytes: bytes,
        language: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Transcribe audio bytes using mlx-audio or mlx-whisper.
        Returns dict with keys: text, language, confidence, engine.
        Returns None if mlx-audio is not available or transcription fails.
        """
        if not MLX_AVAILABLE or not audio_bytes or len(audio_bytes) < 44:
            return None

        import tempfile
        tmp_path = None
        try:
            self._ensure_loaded()
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            target_lang = None
            if language and language.lower() not in ("auto", "none", ""):
                # normalize e.g. "en-IN" -> "en"
                target_lang = language.split("-")[0].lower()

            if self.backend == "mlx_audio" and hasattr(self.model, "transcribe"):
                res = self.model.transcribe(tmp_path, language=target_lang)
            elif self.backend == "mlx_whisper":
                import mlx_whisper  # type: ignore[import-not-found]
                res = mlx_whisper.transcribe(
                    tmp_path,
                    path_or_hf_repo=self.model_name,
                    language=target_lang
                )
            else:
                return None

            text = ""
            detected_lang = target_lang or "en"
            if isinstance(res, dict):
                text = res.get("text", "").strip()
                detected_lang = res.get("language", detected_lang)
            elif isinstance(res, str):
                text = res.strip()

            if text:
                return {
                    "text": text,
                    "language": detected_lang,
                    "confidence": 0.96,
                    "engine": f"MLX-Audio ({self.model_name})"
                }
            return None

        except Exception as err:
            logger.warning(f"[MLX-Audio] Transcription error: {err}")
            return None
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass


# Singleton transcriber instance
mlx_transcriber = MLXAudioTranscriber()
