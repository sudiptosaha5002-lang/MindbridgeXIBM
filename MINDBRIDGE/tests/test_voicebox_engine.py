"""
Unit Tests for MindBridge Voicebox Engine (Jamie Pine Architecture)
===================================================================
Tests:
1. Voicebox studio personas catalog & language resolution
2. Sentence-level natural lookahead chunker
3. Neural speech synthesis in English, Bengali, and Hindi
4. Sentence-split chunk synthesis with metadata
5. Voicebox Flask API endpoints (/api/voicebox/voices, synthesize, status)
"""

import unittest
import json
import sys
import os

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from backend.voicebox_engine import voicebox_engine, split_text_into_natural_chunks, VOICEBOX_STUDIO_PERSONAS  # type: ignore[import-not-found]
from backend.server import app  # type: ignore[import-not-found]
from backend.mlx_audio_stt import mlx_transcriber, MLXAudioTranscriber  # type: ignore[import-not-found]

class TestVoiceboxEngine(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_voicebox_personas_catalog(self):
        """Verify presence of diverse multilingual therapeutic personas."""
        personas = voicebox_engine.get_personas()
        self.assertGreaterEqual(len(personas), 8)
        
        persona_ids = [p["id"] for p in personas]
        self.assertIn("en_serene_aria", persona_ids)
        self.assertIn("bn_empathetic_tanishaa", persona_ids)
        self.assertIn("hi_compassionate_swara", persona_ids)
        self.assertIn("es_calida_elena", persona_ids)
        self.assertIn("pt_serena_francisca", persona_ids)

        # Test language resolution
        self.assertEqual(voicebox_engine.resolve_persona("bn-IN")["id"], "bn_empathetic_tanishaa")
        self.assertEqual(voicebox_engine.resolve_persona("hi-IN")["id"], "hi_compassionate_swara")
        self.assertEqual(voicebox_engine.resolve_persona("en-US")["id"], "en_serene_aria")

    def test_sentence_chunker(self):
        """Verify conversational sentence splitting without mid-phrase cuts."""
        text = "Hello there! I am right here with you. Take a gentle breath, and let's explore this together."
        chunks = split_text_into_natural_chunks(text)
        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0], "Hello there!")
        self.assertEqual(chunks[1], "I am right here with you.")
        self.assertEqual(chunks[2], "Take a gentle breath, and let's explore this together.")

        # Bengali Dari punctuation test
        bn_text = "আমি আপনার সাথে আছি। আপনি কেমন অনুভব করছেন?"
        bn_chunks = split_text_into_natural_chunks(bn_text)
        self.assertEqual(len(bn_chunks), 2)
        self.assertEqual(bn_chunks[0], "আমি আপনার সাথে আছি।")

    def test_voicebox_synthesis(self):
        """Verify neural synthesis returns valid audio bytes."""
        audio_en = voicebox_engine.synthesize("MindBridge Voicebox synthesis test.", persona_id="en_serene_aria")
        self.assertIsInstance(audio_en, bytes)
        self.assertGreater(len(audio_en), 1000)

        # Bengali Synthesis
        audio_bn = voicebox_engine.synthesize("স্বাগতম মাইন্ডব্রিজে।", persona_id="bn_empathetic_tanishaa")
        self.assertIsInstance(audio_bn, bytes)
        self.assertGreater(len(audio_bn), 1000)

    def test_voicebox_synthesize_chunks(self):
        """Verify structured chunking for sample-accurate scheduling."""
        text = "First thought. Second thought. Third peaceful reflection."
        chunks = voicebox_engine.synthesize_chunks(text, persona_id="en_serene_aria")
        self.assertEqual(len(chunks), 3)
        for i, c in enumerate(chunks):
            self.assertEqual(c["chunk_index"], i)
            self.assertEqual(c["total_chunks"], 3)
            self.assertGreater(len(c["audio_bytes"]), 500)

    def test_api_voices_endpoint(self):
        """Test GET /api/voicebox/voices."""
        res = self.app.get("/api/voicebox/voices")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertGreaterEqual(len(data["voices"]), 8)

    def test_api_synthesize_endpoint_json(self):
        """Test POST /api/voicebox/synthesize with JSON format."""
        payload = {
            "text": "Voicebox is active and clear.",
            "persona_id": "en_serene_aria",
            "format": "json",
            "split_chunks": False
        }
        res = self.app.post(
            "/api/voicebox/synthesize",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("audio_base64", data)
        self.assertGreater(len(data["audio_base64"]), 100)

    def test_api_synthesize_endpoint_audio(self):
        """Test POST /api/voicebox/synthesize with audio/mpeg format."""
        payload = {
            "text": "Voicebox streaming test.",
            "persona_id": "en_warm_jenny",
            "format": "audio"
        }
        res = self.app.post(
            "/api/voicebox/synthesize",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content_type, "audio/mpeg")
        self.assertGreater(len(res.data), 1000)

    def test_api_synthesize_split_chunks(self):
        """Test POST /api/voicebox/synthesize with split_chunks=True."""
        payload = {
            "text": "Welcome to MindBridge. Take a calm breath.",
            "persona_id": "en_serene_aria",
            "split_chunks": True
        }
        res = self.app.post(
            "/api/voicebox/synthesize",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertEqual(len(data["chunks"]), 2)
        self.assertIn("audio_base64", data["chunks"][0])

    def test_api_transcribe_endpoint(self):
        """Test POST /api/voicebox/transcribe with synthetic WAV audio."""
        import wave, io, struct
        bio = io.BytesIO()
        with wave.open(bio, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            # 0.5s of gentle sine wave audio
            import math
            frames = bytearray()
            for i in range(8000):
                val = int(3000 * math.sin(2 * math.pi * 440 * i / 16000))
                frames.extend(struct.pack('<h', val))
            wf.writeframes(frames)
        bio.seek(0)

        data = {
            'audio': (bio, 'test_answer.wav'),
            'language': 'en'
        }
        res = self.app.post(
            '/api/voicebox/transcribe',
            data=data,
            content_type='multipart/form-data'
        )
        self.assertEqual(res.status_code, 200)
        res_data = json.loads(res.data)
        self.assertEqual(res_data["status"], "success")
        self.assertIn("transcription", res_data)
        self.assertIn("text", res_data)

    def test_mlx_audio_stt_adapter(self):
        """Verify MLX-Audio STT adapter behavior, availability detection, and graceful fallback."""
        self.assertIsInstance(mlx_transcriber, MLXAudioTranscriber)
        # On non-Apple Silicon (Windows/Linux), is_available() returns False gracefully
        # On Apple Silicon macOS, is_available() returns True
        is_avail = mlx_transcriber.is_available()
        self.assertIsInstance(is_avail, bool)

        # Transcribing with unavailable or dummy bytes should return None without crashing
        res = mlx_transcriber.transcribe_audio_bytes(b"dummy_short_audio", language="en")
        if not is_avail:
            self.assertIsNone(res)

    def test_api_transcribe_with_tone_analysis(self):
        """Verify POST /api/voicebox/transcribe supports analyze_tone=true."""
        import wave, io, struct, math
        bio = io.BytesIO()
        with wave.open(bio, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            frames = bytearray()
            for i in range(8000):
                val = int(2500 * math.sin(2 * math.pi * 350 * i / 16000))
                frames.extend(struct.pack('<h', val))
            wf.writeframes(frames)
        bio.seek(0)

        data = {
            'audio': (bio, 'test_answer_tone.wav'),
            'language': 'en',
            'analyze_tone': 'true',
            'session_id': 'test_session_vb',
            'question_id': 'test_q1'
        }
        res = self.app.post(
            '/api/voicebox/transcribe?analyze_tone=true',
            data=data,
            content_type='multipart/form-data'
        )
        self.assertEqual(res.status_code, 200)
        res_data = json.loads(res.data)
        self.assertEqual(res_data["status"], "success")
        self.assertIn("transcription", res_data)
        self.assertIn("text", res_data)


if __name__ == "__main__":
    unittest.main()


