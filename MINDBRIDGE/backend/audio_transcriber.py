"""
MindBridge Secure Multilingual Speech-to-Text Engine
Supports MediaRecorder WebM/Opus, MP4, OGG, and WAV.
Primary STT: Self-hosted faster-whisper (CTranslate2) with multilingual Indian & Global language support.
Fallback STT: High-fidelity Google Acoustic Bridge (en-IN, hi-IN, bn-IN, etc.) and OpenAI Cloud Whisper.
"""

import os
import io
import time
import wave
import logging
import tempfile
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("MindBridgeVoice")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Supported language codes map
LANGUAGE_MAP = {
    "auto": None,
    "en": "en",
    "en-US": "en",
    "en-IN": "en",
    "hi": "hi",
    "hi-IN": "hi",
    "bn": "bn",
    "bn-IN": "bn",
    "ta": "ta",
    "ta-IN": "ta",
    "te": "te",
    "te-IN": "te",
    "es": "es",
    "es-ES": "es",
    "pt": "pt",
    "pt-BR": "pt"
}

SPEECHREC_LOCALE_MAP = {
    "en": "en-IN",
    "en-US": "en-US",
    "en-IN": "en-IN",
    "hi": "hi-IN",
    "hi-IN": "hi-IN",
    "bn": "bn-IN",
    "bn-IN": "bn-IN",
    "ta": "ta-IN",
    "ta-IN": "ta-IN",
    "te": "te-IN",
    "te-IN": "te-IN",
    "es": "es-ES",
    "es-ES": "es-ES",
    "pt": "pt-BR",
    "pt-BR": "pt-BR",
    "auto": "en-IN"
}

class AudioConverter:
    """Decodes browser audio (WebM/Opus, MP4, OGG, WAV) into standard 16kHz mono 16-bit PCM WAV."""

    @staticmethod
    def to_wav_16k_mono(input_bytes: bytes) -> bytes:
        if not input_bytes or len(input_bytes) < 44:
            raise ValueError("Audio data is empty or too short.")

        # Check if already a standard WAV
        if input_bytes[:4] == b"RIFF" and b"WAVE" in input_bytes[:16]:
            try:
                with wave.open(io.BytesIO(input_bytes), "rb") as wf:
                    channels = wf.getnchannels()
                    framerate = wf.getframerate()
                    sampwidth = wf.getsampwidth()
                    if channels == 1 and framerate == 16000 and sampwidth == 2:
                        return input_bytes
            except Exception:
                pass

        # Use PyAV (av) to decode WebM, Opus, MP4, AAC, OGG, or any WAV format
        try:
            import av
            input_io = io.BytesIO(input_bytes)
            container = av.open(input_io)
            
            # Setup 16kHz Mono 16-bit PCM resampler
            resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)
            out_io = io.BytesIO()
            
            with wave.open(out_io, "wb") as wav_out:
                wav_out.setnchannels(1)
                wav_out.setsampwidth(2)
                wav_out.setframerate(16000)
                
                audio_streams = [s for s in container.streams if s.type == "audio"]
                if not audio_streams:
                    raise ValueError("No audio stream found in container.")
                
                has_frames = False
                for frame in container.decode(audio=0):
                    has_frames = True
                    for resampled in resampler.resample(frame):
                        wav_out.writeframes(resampled.to_ndarray().tobytes())
                
                if not has_frames:
                    raise ValueError("No audio frames decoded from container.")
            
            return out_io.getvalue()
        except Exception as av_err:
            logger.warning(f"[AudioConverter] PyAV decode note: {av_err}. Attempting raw WAV fallback.")
            # If PyAV had issue, check if standard wave can read it
            try:
                with wave.open(io.BytesIO(input_bytes), "rb") as wf:
                    return input_bytes
            except Exception:
                raise ValueError(f"Could not decode audio format: {av_err}")


class FasterWhisperSTT:
    """Self-hosted faster-whisper (CTranslate2) optimized for CPU/GPU."""
    
    _instance = None
    _model = None

    def __init__(self, model_size: str = "tiny"):
        self.model_size = os.environ.get("WHISPER_MODEL", model_size)
        self.device = "cpu"
        self.compute_type = "int8"
        self._init_attempted = False

    def _load_model(self):
        if FasterWhisperSTT._model is None and not self._init_attempted:
            self._init_attempted = True
            try:
                from faster_whisper import WhisperModel
                import torch
                if torch.cuda.is_available():
                    self.device = "cuda"
                    self.compute_type = "float16"
                logger.info(f"[FasterWhisper] Loading '{self.model_size}' model on {self.device} ({self.compute_type})...")
                FasterWhisperSTT._model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                    download_root=os.path.join(tempfile.gettempdir(), "whisper_cache")
                )
                logger.info(f"[FasterWhisper] Model '{self.model_size}' initialized.")
            except Exception as e:
                logger.warning(f"[FasterWhisper] Initialization note (will use acoustic fallback): {e}")
                FasterWhisperSTT._model = None

    def transcribe(self, wav_bytes: bytes, language: str = "auto") -> Optional[Dict[str, Any]]:
        if FasterWhisperSTT._model is None:
            self._load_model()
        if FasterWhisperSTT._model is None:
            return None

        t0 = time.time()
        temp_wav = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_wav = f.name
                f.write(wav_bytes)

            lang_code = LANGUAGE_MAP.get(language)
            segments, info = FasterWhisperSTT._model.transcribe(
                temp_wav,
                language=lang_code,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=400)
            )

            text = " ".join([seg.text.strip() for seg in segments]).strip()
            elapsed_ms = round((time.time() - t0) * 1000, 1)

            detected_lang = info.language if hasattr(info, "language") else language
            return {
                "text": text,
                "detected_language": detected_lang,
                "confidence": getattr(info, "language_probability", 0.95),
                "latency_ms": elapsed_ms,
                "engine": f"faster-whisper ({self.model_size})",
                "status": "success" if text else "silence"
            }
        except Exception as e:
            logger.warning(f"[FasterWhisper] Transcribe error: {e}")
            return None
        finally:
            if temp_wav and os.path.exists(temp_wav):
                try:
                    os.unlink(temp_wav)
                except Exception:
                    pass


class GoogleAcousticSTT:
    """High-fidelity multilingual bridge supporting en-IN, hi-IN, bn-IN, etc."""

    @staticmethod
    def transcribe(wav_bytes: bytes, language: str = "en-IN") -> Dict[str, Any]:
        t0 = time.time()
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            r.energy_threshold = 25
            r.dynamic_energy_threshold = False

            with sr.AudioFile(io.BytesIO(wav_bytes)) as source:
                audio_data = r.record(source)

            target_locale = SPEECHREC_LOCALE_MAP.get(language, "en-IN")
            text = r.recognize_google(audio_data, language=target_locale)
            elapsed_ms = round((time.time() - t0) * 1000, 1)
            
            return {
                "text": text.strip() if text else "",
                "detected_language": target_locale,
                "latency_ms": elapsed_ms,
                "engine": "Google Cloud Acoustic Bridge",
                "status": "success" if text else "silence"
            }
        except sr.UnknownValueError:
            return {
                "text": "",
                "detected_language": language,
                "latency_ms": round((time.time() - t0) * 1000, 1),
                "engine": "Google Cloud Acoustic Bridge",
                "status": "silence"
            }
        except Exception as e:
            logger.warning(f"[GoogleAcousticSTT] Note: {e}")
            return {
                "text": "",
                "detected_language": language,
                "latency_ms": round((time.time() - t0) * 1000, 1),
                "engine": "Google Cloud Acoustic Bridge",
                "status": "error",
                "error": str(e)
            }


class CloudWhisperAPI:
    """OpenAI Cloud Whisper API if OPENAI_API_KEY is configured."""

    @staticmethod
    def transcribe(wav_bytes: bytes, language: str = "auto") -> Optional[Dict[str, Any]]:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return None

        t0 = time.time()
        temp_wav = None
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_wav = f.name
                f.write(wav_bytes)

            with open(temp_wav, "rb") as af:
                lang = LANGUAGE_MAP.get(language)
                kwargs = {"model": "whisper-1", "file": af}
                if lang:
                    kwargs["language"] = lang
                res = client.audio.transcriptions.create(**kwargs)

            text = res.text.strip() if hasattr(res, "text") else ""
            elapsed_ms = round((time.time() - t0) * 1000, 1)
            return {
                "text": text,
                "detected_language": language,
                "latency_ms": elapsed_ms,
                "engine": "OpenAI Cloud Whisper API",
                "status": "success" if text else "silence"
            }
        except Exception as e:
            logger.warning(f"[CloudWhisperAPI] Error: {e}")
            return None
        finally:
            if temp_wav and os.path.exists(temp_wav):
                try:
                    os.unlink(temp_wav)
                except Exception:
                    pass


class SpeechTranscriberManager:
    """
    Unified Orchestrator:
    1. Decodes incoming audio (WebM/Opus, MP4, WAV, OGG) -> 16kHz Mono WAV.
    2. Primary STT: Faster-Whisper (self-hosted).
    3. Fallback 1: Google Acoustic Bridge (high-fidelity Indian & international locales).
    4. Fallback 2: OpenAI Cloud Whisper (if API key present).
    5. Automatic cleanup of any temporary artifacts.
    """

    def __init__(self):
        self.faster_whisper = FasterWhisperSTT(model_size=os.environ.get("WHISPER_MODEL", "tiny"))

    def transcribe_audio_bytes(self, raw_audio_bytes: bytes, language: str = "en-IN") -> Dict[str, Any]:
        t0 = time.time()
        if not raw_audio_bytes or len(raw_audio_bytes) < 44:
            return {
                "status": "silence",
                "text": "",
                "message": "No audio data received or audio clip is empty."
            }

        # Step 1: Decode to 16kHz Mono 16-bit PCM WAV
        try:
            wav_bytes = AudioConverter.to_wav_16k_mono(raw_audio_bytes)
        except Exception as conv_err:
            logger.warning(f"[AudioConverter] Conversion error: {conv_err}")
            # Try raw bytes directly if already wav
            wav_bytes = raw_audio_bytes

        # Step 2: Try Faster-Whisper Primary Engine
        fw_res = self.faster_whisper.transcribe(wav_bytes, language=language)
        if fw_res and fw_res.get("text"):
            fw_res["total_latency_ms"] = round((time.time() - t0) * 1000, 1)
            return fw_res

        # Step 3: Try Google Acoustic Bridge Fallback (Supports en-IN, hi-IN, bn-IN, etc.)
        g_res = GoogleAcousticSTT.transcribe(wav_bytes, language=language)
        if g_res and g_res.get("text"):
            g_res["total_latency_ms"] = round((time.time() - t0) * 1000, 1)
            return g_res

        # Step 4: Try OpenAI Cloud Whisper API if configured
        cloud_res = CloudWhisperAPI.transcribe(wav_bytes, language=language)
        if cloud_res and cloud_res.get("text"):
            cloud_res["total_latency_ms"] = round((time.time() - t0) * 1000, 1)
            return cloud_res

        # If silence or no speech was discernable across engines
        return {
            "status": "silence",
            "text": "",
            "detected_language": language,
            "message": "Could not discern clear speech. Please speak closer to your microphone.",
            "total_latency_ms": round((time.time() - t0) * 1000, 1)
        }


# Global singleton transcriber
transcriber_manager = SpeechTranscriberManager()
voice_transcriber = transcriber_manager
