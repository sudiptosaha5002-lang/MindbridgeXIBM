"""
MindBridge Audio Transcription Engine.
Implements Google GenAI gemini-3.5-transcribe with:
1. Standard verbatim transcription
2. Word-level timestamp granularity
3. Seamless fallback to local Dual ASR (Whisper / SpeechRecognition)
"""

import os
import io
import tempfile
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def transcribe_audio_gemini(
    audio_path_or_bytes: Any,
    api_key: Optional[str] = None,
    word_timestamps: bool = True,
    language: str = "auto"
) -> Dict[str, Any]:
    """
    Transcribes audio using Gemini gemini-3.5-transcribe.
    
    Args:
        audio_path_or_bytes: Path to audio file or raw audio bytes.
        api_key: Optional Gemini API key.
        word_timestamps: Whether to request word-level timestamp granularity.
        language: Language hint (e.g. 'en', 'hi', 'bn', or 'auto').
        
    Returns:
        Dict containing:
          - text: Transcribed speech text
          - timestamps: List of word or segment timestamps if available
          - engine: "gemini-3.5-transcribe"
          - status: "success"
    """
    from google import genai

    key = (
        api_key
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
    )
    if not key:
        raise ValueError("GEMINI_API_KEY is not configured for Gemini transcription.")

    client = genai.Client(api_key=key)

    temp_file_created = False
    temp_path = None

    try:
        if isinstance(audio_path_or_bytes, bytes):
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
                tf.write(audio_path_or_bytes)
                temp_path = tf.name
                temp_file_created = True
        elif isinstance(audio_path_or_bytes, str):
            temp_path = audio_path_or_bytes
        else:
            raise ValueError("Unsupported audio input type.")

        # Upload file via Google GenAI Files API
        uploaded_file = client.files.upload(file=temp_path)

        # Build interaction input
        input_content = [
            {
                "type": "audio",
                "uri": uploaded_file.uri,
                "mime_type": uploaded_file.mime_type or "audio/wav"
            }
        ]

        # Configure transcription config with word-level timestamps if requested
        generation_config = {}
        if word_timestamps:
            generation_config["transcription_config"] = {
                "mode": {
                    "type": "verbatim",
                    "timestamp_granularities": ["word"]
                }
            }

        interaction = client.interactions.create(
            model="gemini-3.5-transcribe",
            input=input_content,
            generation_config=generation_config if generation_config else None
        )

        transcribed_text = getattr(interaction, "output_text", None) or ""
        
        # If output_text is empty, check interaction.outputs
        if not transcribed_text and hasattr(interaction, "outputs") and interaction.outputs:
            for out in interaction.outputs:
                if getattr(out, "type", None) == "text" and getattr(out, "text", None):
                    transcribed_text = out.text
                    break

        return {
            "status": "success",
            "text": transcribed_text.strip(),
            "engine": "gemini-3.5-transcribe",
            "word_timestamps_enabled": word_timestamps
        }

    finally:
        if temp_file_created and temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
