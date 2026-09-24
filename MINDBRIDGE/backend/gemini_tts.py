"""
MindBridge Gemini Neural Text-To-Speech (TTS) Engine.
Integrates Google GenAI SDK (gemini-3.1-flash-tts-preview & Multimodal Live Audio)
to produce humanized, compassionate speech with voice models like Kore, Aoede, Puck, and Fenrir.
Supports:
1. Single-speaker TTS with in-memory WAV conversion
2. Streaming audio chunk generation (stream=True)
3. Multi-speaker dialogue synthesis (e.g. Therapist + Client co-regulation roleplay)
"""

import os
import io
import wave
import base64
import logging
from typing import List, Dict, Generator

logger = logging.getLogger(__name__)

def pcm_to_wav_bytes(pcm_data: bytes, channels: int = 1, rate: int = 24000, sample_width: int = 2) -> bytes:
    """
    Packages raw PCM linear audio bytes into a standard playable WAV file in-memory.
    """
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_data)
    return buf.getvalue()


def synthesize_speech_gemini(text: str, voice_name: str = "Kore", api_key: str = None) -> bytes:
    """
    Synthesizes speech using Google GenAI SDK.
    Supports gemini-3.1-flash-tts-preview via client.interactions.create,
    with automatic failover to client.models.generate_content.
    
    Returns:
        bytes: Playable WAV audio data.
    """
    if not text or not text.strip():
        raise ValueError("Cannot synthesize empty text.")

    from google import genai
    from google.genai import types

    # Resolve API key from argument, environment, or settings
    key = (
        api_key
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
    )
    if not key:
        raise ValueError("GEMINI_API_KEY is not configured in environment or request.")

    client = genai.Client(api_key=key)

    # Strategy 1: Interactions API with gemini-3.1-flash-tts-preview
    try:
        interaction = client.interactions.create(
            model="gemini-3.1-flash-tts-preview",
            input=text,
            response_format={"type": "audio"},
            generation_config={
                "speech_config": [
                    {"voice": voice_name}
                ]
            }
        )

        audio_b64 = None
        # Check both direct output_audio (user snippet format) and outputs array (SDK format)
        if hasattr(interaction, "output_audio") and interaction.output_audio:
            audio_b64 = getattr(interaction.output_audio, "data", None)
        
        if not audio_b64 and hasattr(interaction, "outputs") and interaction.outputs:
            for out in interaction.outputs:
                if getattr(out, "type", None) == "audio" and getattr(out, "data", None):
                    audio_b64 = out.data
                    break

        if audio_b64:
            pcm_bytes = base64.b64decode(audio_b64)
            return pcm_to_wav_bytes(pcm_bytes, channels=1, rate=24000, sample_width=2)

    except Exception as e:
        logger.warning(f"[Gemini TTS] Interactions preview API call note: {e}. Trying generate_content fallback...")

    # Strategy 2: Standard Multimodal Audio API
    try:
        config = types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
                )
            )
        )
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=text,
            config=config
        )

        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if getattr(part, "inline_data", None) and getattr(part.inline_data, "data", None):
                    audio_bytes = part.inline_data.data
                    mime = getattr(part.inline_data, "mime_type", "") or ""
                    if "wav" in mime.lower():
                        return audio_bytes
                    return pcm_to_wav_bytes(audio_bytes, channels=1, rate=24000, sample_width=2)

    except Exception as e2:
        logger.error(f"[Gemini TTS] generate_content audio fallback failed: {e2}")
        raise e2

    raise RuntimeError("No audio data returned from Gemini TTS engine.")


def synthesize_speech_gemini_stream(text: str, voice_name: str = "Kore", api_key: str = None) -> Generator[bytes, None, None]:
    """
    Streams audio chunks using Gemini interactions streaming API (stream=True).
    Yields raw linear PCM audio chunk bytes.
    """
    from google import genai

    key = (
        api_key
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
    )
    if not key:
        raise ValueError("GEMINI_API_KEY is not configured in environment or request.")

    client = genai.Client(api_key=key)

    stream = client.interactions.create(
        model="gemini-3.1-flash-tts-preview",
        input=text,
        response_format={"type": "audio"},
        generation_config={
            "speech_config": [
                {"voice": voice_name}
            ]
        },
        stream=True
    )

    for event in stream:
        event_type = getattr(event, "event_type", None)
        if event_type == "step.delta":
            delta = getattr(event, "delta", None)
            if delta and getattr(delta, "type", None) == "audio" and getattr(delta, "data", None):
                chunk_bytes = base64.b64decode(delta.data)
                yield chunk_bytes


def synthesize_multispeaker_gemini(dialogue_prompt: str, speakers_config: List[Dict[str, str]] = None, api_key: str = None) -> bytes:
    """
    Synthesizes multi-speaker conversational audio using Gemini TTS.
    Example speakers_config:
      [
        {"speaker": "MindBridge", "voice": "Kore"},
        {"speaker": "User", "voice": "Puck"}
      ]
    """
    from google import genai

    key = (
        api_key
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
    )
    if not key:
        raise ValueError("GEMINI_API_KEY is not configured in environment or request.")

    if not speakers_config:
        speakers_config = [
            {"speaker": "MindBridge", "voice": "Kore"},
            {"speaker": "User", "voice": "Puck"}
        ]

    client = genai.Client(api_key=key)
    interaction = client.interactions.create(
        model="gemini-3.1-flash-tts-preview",
        input=dialogue_prompt,
        response_format={"type": "audio"},
        generation_config={
            "speech_config": speakers_config
        }
    )

    audio_b64 = None
    if hasattr(interaction, "output_audio") and interaction.output_audio:
        audio_b64 = getattr(interaction.output_audio, "data", None)
    if not audio_b64 and hasattr(interaction, "outputs") and interaction.outputs:
        for out in interaction.outputs:
            if getattr(out, "type", None) == "audio" and getattr(out, "data", None):
                audio_b64 = out.data
                break

    if audio_b64:
        pcm = base64.b64decode(audio_b64)
        return pcm_to_wav_bytes(pcm, channels=1, rate=24000, sample_width=2)

    raise RuntimeError("No multi-speaker audio returned from Gemini TTS.")
