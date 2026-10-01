
"""
Unit Tests for MindBridge Voice-Capture & Voice-Tone Emotion Analysis Module
Tests acoustic feature extraction, CNN-BiLSTM SER neural model, session aggregation,
and backend API endpoints (/api/analyze_voice_tone, /api/transcribe, /api/screener/evaluate).
"""

import os
import io
import sys
import wave
import struct
import unittest
import numpy as np

# Ensure backend path is available
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

import voice_tone_analyzer as vta  # type: ignore[import-not-found]
from server import app  # type: ignore[import-not-found]
import database as db  # type: ignore[import-not-found]


class TestVoiceToneModule(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        # Generate synthetic 16kHz audio: 440Hz sine wave, 1.2 seconds duration
        cls.sample_rate = 16000
        cls.duration = 1.2
        num_samples = int(cls.sample_rate * cls.duration)
        t = np.linspace(0, cls.duration, num_samples, endpoint=False)
        cls.pcm_sine = (np.sin(2 * np.pi * 440 * t) * 0.45).astype(np.float32)

        # Create standard WAV bytes
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(cls.sample_rate)
            pcm_int16 = (cls.pcm_sine * 32767.0).astype(np.int16)
            wf.writeframes(pcm_int16.tobytes())
        cls.wav_bytes = buf.getvalue()

    def test_01_acoustic_prosodic_feature_extraction(self):
        """Verify pitch, energy, speaking rate, and voiced ratio extraction."""
        prosody = vta.AcousticProsodicExtractor.extract_prosody(self.pcm_sine)
        self.assertIn("avg_pitch_hz", prosody)
        self.assertIn("avg_energy_db", prosody)
        self.assertIn("speaking_rate_units_per_sec", prosody)
        self.assertIn("voiced_ratio", prosody)

        # 440Hz sine wave should have pitch estimate near 440Hz
        self.assertAlmostEqual(prosody["avg_pitch_hz"], 440.0, delta=15.0)
        # Energy should be higher than silence (-40 dB)
        self.assertGreater(prosody["avg_energy_db"], -25.0)
        self.assertGreater(prosody["voiced_ratio"], 0.8)

    def test_02_mfcc_feature_shape(self):
        """Verify 26-channel MFCC + Delta extraction matches CNN-BiLSTM input shape [26, 64]."""
        mfcc = vta.AcousticProsodicExtractor.extract_mfcc(self.pcm_sine, num_frames_target=64)
        self.assertEqual(mfcc.shape, (26, 64))
        self.assertFalse(np.isnan(mfcc).any())

    def test_03_cnn_bilstm_forward_pass(self):
        """Verify neural model forward pass produces valid 5-class distribution summing to 1.0."""
        analyzer = vta.VoiceToneAnalyzer()
        res = analyzer.analyze_audio_clip(self.wav_bytes)

        self.assertEqual(res["status"], "success")
        self.assertIn("dominant_tone", res)
        self.assertIn("tone_distribution", res)
        dist = res["tone_distribution"]

        # 5 tone classes present
        for c in vta.TONE_CLASSES:
            self.assertIn(c, dist)
            self.assertGreaterEqual(dist[c], 0.0)
            self.assertLessEqual(dist[c], 1.0)

        # Sum of probabilities must equal ~1.0
        total_prob = sum(dist.values())
        self.assertAlmostEqual(total_prob, 1.0, places=2)

    def test_04_session_tone_aggregation(self):
        """Verify session tone aggregation over multiple answers."""
        aggregator = vta.VoiceToneSessionAggregator()
        session_id = "test-session-aggr-101"

        analyzer = vta.VoiceToneAnalyzer()
        res1 = analyzer.analyze_audio_clip(self.wav_bytes)
        res2 = analyzer.analyze_audio_clip(self.wav_bytes)

        aggregator.record_answer_tone(session_id, "q1", res1)
        aggregator.record_answer_tone(session_id, "q2", res2)

        summary = aggregator.get_session_summary(session_id)
        self.assertIsNotNone(summary)
        self.assertEqual(summary["total_voice_answers"], 2)
        self.assertIn("dominant_tone", summary)
        self.assertIn("prosodic_features", summary)
        self.assertIn("interpretation_text", summary)
        self.assertIn("disclaimer", summary)
        self.assertIn("NOT a clinical psychological", summary["disclaimer"])

    def test_05_api_analyze_voice_tone_endpoint(self):
        """Test POST /api/analyze_voice_tone accepts audio and returns expected schema."""
        response = self.client.post(
            "/api/analyze_voice_tone",
            data={
                "audio": (io.BytesIO(self.wav_bytes), "sample.wav"),
                "session_id": "test-api-session-1",
                "question_id": "q1"
            },
            content_type="multipart/form-data"
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("voice_tone", data)
        self.assertIn("dominant_tone", data["voice_tone"])
        self.assertIn("disclaimer", data)

    def test_06_api_transcribe_with_tone_analysis(self):
        """Test POST /api/transcribe includes voice tone analysis when analyze_tone=true."""
        response = self.client.post(
            "/api/transcribe?analyze_tone=true&session_id=test-api-session-2&question_id=q2",
            data={
                "audio": (io.BytesIO(self.wav_bytes), "recording.webm")
            },
            content_type="multipart/form-data"
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("voice_tone", data)
        self.assertIn("dominant_tone", data["voice_tone"])

    def test_07_screener_evaluate_includes_voice_tone(self):
        """Test /api/screener/evaluate embeds voice_tone_summary when available."""
        import mental_screening as ms  # type: ignore[import-not-found]
        user_id = "user-vt-test"
        session_id = db.create_screening_session(user_id, ["q1", "q2"])
        ms.screening_engine.record_answer(session_id, user_id, "q1", "Feeling okay", input_mode="voice")

        # Record tone data in session aggregator
        analyzer = vta.VoiceToneAnalyzer()
        res = analyzer.analyze_audio_clip(self.wav_bytes)
        vta.session_tone_aggregator.record_answer_tone(session_id, "q1", res)

        # Call evaluate
        response = self.client.post(
            "/api/screener/evaluate",
            json={"session_id": session_id}
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        result = data.get("result", {})
        self.assertIn("voice_tone_summary", result)
        self.assertEqual(result["voice_tone_summary"]["dominant_tone"], res["dominant_tone"])


if __name__ == "__main__":
    unittest.main()
