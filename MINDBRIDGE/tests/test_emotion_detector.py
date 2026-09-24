"""
Unit Tests for MindBridge Emotion Detection & Classification Engine.
Verifies emotion categorization, intensity scoring, clinical sensitivity flags,
and multi-turn contextual scoring in English, Bengali, and Hindi.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from emotion_detector import emotion_detector

class TestEmotionDetector(unittest.TestCase):
    def test_sadness_and_hopelessness_detection(self):
        text = "I feel completely hopeless and crying all day, nothing matters anymore."
        res = emotion_detector.detect_emotion(text)
        self.assertTrue(res["is_emotional"])
        emotions = [e["label"] for e in res["detected_emotions"]]
        self.assertIn("sadness", emotions)
        self.assertIn("hopelessness", emotions)
        self.assertTrue(res["needs_emotion_interview"])
        self.assertIn(res["intensity"], ["moderate", "high"])

    def test_anxiety_and_overwhelm_detection(self):
        text = "I'm having racing thoughts and panic, completely overwhelmed by my job deadlines!"
        res = emotion_detector.detect_emotion(text)
        self.assertTrue(res["is_emotional"])
        emotions = [e["label"] for e in res["detected_emotions"]]
        self.assertIn("anxiety", emotions)
        self.assertIn("overwhelm", emotions)
        self.assertTrue(res["needs_emotion_interview"])

    def test_bengali_emotion_detection(self):
        text = "আমার মন খুব খারাপ এবং ভীষণ কষ্ট হচ্ছে, খুব একা লাগছে।"
        res = emotion_detector.detect_emotion(text, language="bn")
        self.assertTrue(res["is_emotional"])
        emotions = [e["label"] for e in res["detected_emotions"]]
        self.assertTrue("sadness" in emotions or "loneliness" in emotions)
        self.assertTrue(res["needs_emotion_interview"])

    def test_hindi_emotion_detection(self):
        text = "मुझे बहुत ज्यादा डर और घबराहट हो रही है, दिल बहुत रो रहा है।"
        res = emotion_detector.detect_emotion(text, language="hi")
        self.assertTrue(res["is_emotional"])
        emotions = [e["label"] for e in res["detected_emotions"]]
        self.assertTrue("anxiety" in emotions or "fear" in emotions)
        self.assertTrue(res["needs_emotion_interview"])

    def test_neutral_non_emotional_input(self):
        text = "What time is my appointment scheduled for tomorrow?"
        res = emotion_detector.detect_emotion(text)
        self.assertFalse(res["needs_emotion_interview"])
        self.assertEqual(res["sensitivity_flags"], [])

    def test_sensitivity_flag_detection(self):
        text = "I feel like hurting myself and I don't want to live anymore."
        res = emotion_detector.detect_emotion(text)
        self.assertTrue(res["is_emotional"])
        self.assertTrue(res["needs_emotion_interview"])
        self.assertEqual(res["intensity"], "high")
        self.assertTrue("suicidal_feelings" in res["sensitivity_flags"] or "self_harm_thoughts" in res["sensitivity_flags"])

    def test_contextual_multi_turn_scoring(self):
        context = [
            {"sender": "user", "content": "I feel so lonely in this new city."},
            {"sender": "mindbridge", "content": "I hear you, it takes time to adjust."},
            {"sender": "user", "content": "Everything feels heavy."}
        ]
        text = "It's just hard right now."
        res = emotion_detector.detect_emotion(text, context_messages=context)
        self.assertTrue(res["is_emotional"])
        self.assertTrue(res["needs_emotion_interview"])

if __name__ == "__main__":
    unittest.main()
