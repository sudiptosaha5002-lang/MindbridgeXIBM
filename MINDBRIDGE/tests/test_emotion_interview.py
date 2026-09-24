"""
Unit Tests for MindBridge Emotion Interview Module.
Verifies emotion interview session creation, answer processing,
emotion synthesis, and REST API endpoints.
"""

import os
import sys
import json
import unittest
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from server import app
import database as db
from emotion_interview_engine import emotion_interview_engine
from emotion_detector import emotion_detector

class TestEmotionInterviewModule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Configure app for testing
        app.config["TESTING"] = True
        cls.client = app.test_client()
        # Initialize DB
        db.init_db()

    def setUp(self):
        # Setup specific to each test
        self.user_id = "test-user-emo-1"
        self.conversation_id = f"conv_emo_{datetime.now().timestamp()}"

    def test_01_detect_emotion_endpoint(self):
        """Test the /api/detect_emotion endpoint"""
        payload = {
            "text": "I feel extremely anxious and overwhelmed with all this work.",
            "language": "en"
        }
        res = self.client.post("/api/detect_emotion", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["is_emotional"])
        emotions = [e["label"] for e in data["detected_emotions"]]
        self.assertIn("anxiety", emotions)
        self.assertIn("overwhelm", emotions)
        self.assertTrue(data["needs_emotion_interview"])

    def test_02_start_emotion_interview_session(self):
        """Test starting a new emotion interview session"""
        payload = {
            "user_id": self.user_id,
            "conversation_id": self.conversation_id,
            "language": "en",
            "trigger_reason": "test_trigger"
        }
        res = self.client.post("/api/emotion-interview/start", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        
        session = data["session"]
        self.assertIn("session_id", session)
        self.assertEqual(session["current_index"], 0)
        self.assertEqual(session["total_questions"], 10)
        self.assertIsNotNone(session["question"])
        
        # Save session_id for subsequent tests
        self.__class__.session_id = session["session_id"]

    def test_03_submit_emotion_answer_and_progress(self):
        """Test submitting answers and checking session progress"""
        session_id = self.__class__.session_id
        
        # Answer Question 1
        payload1 = {
            "session_id": session_id,
            "user_id": self.user_id,
            "answer": "I feel really stressed and a bit sad today.",
            "input_mode": "text"
        }
        res1 = self.client.post("/api/emotion-interview/answer", json=payload1)
        self.assertEqual(res1.status_code, 200)
        data1 = res1.get_json()["result"]
        self.assertFalse(data1["is_complete"])
        self.assertEqual(data1["current_index"], 1)

        # Skip to the end (mocking by answering the remaining 9 questions)
        for i in range(1, 10):
            payload = {
                "session_id": session_id,
                "user_id": self.user_id,
                "answer": "I try to take deep breaths and walk in nature to cope.", # Healthy coping signal
                "input_mode": "text"
            }
            res = self.client.post("/api/emotion-interview/answer", json=payload)
            data = res.get_json()["result"]

        # The last answer should trigger completion
        self.assertTrue(data["is_complete"])
        self.assertIsNotNone(data["analysis"])
        
        # Verify the analysis
        analysis = data["analysis"]
        self.assertIn("anxiety", analysis["dominant_emotions"])
        self.assertEqual(analysis["coping_style"], "healthy_coping")
        self.assertIn("emotional_state_summary", analysis)

    def test_04_get_completed_session(self):
        """Test fetching a completed session state via API"""
        res = self.client.get(f"/api/emotion-interview/session/{self.__class__.session_id}")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        session = data["session"]
        
        self.assertEqual(session["status"], "completed")
        self.assertEqual(len(session["answers"]), 10)
        
    def test_05_analyze_emotions_endpoint(self):
        """Test the explicit analyze_emotions endpoint with a session ID"""
        payload = {
            "session_id": self.__class__.session_id
        }
        res = self.client.post("/api/analyze_emotions", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("analysis", data)
        self.assertEqual(data["analysis"]["coping_style"], "healthy_coping")

    def test_06_hindi_emotion_questions(self):
        """Verify Hindi questions are retrieved correctly"""
        res = self.client.get("/api/emotion-interview/questions?lang=hi")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["language"], "hi")
        self.assertEqual(len(data["questions"]), 10)
        # Check first question is in Hindi
        q1 = data["questions"][0]
        self.assertTrue(any(ord(c) > 127 for c in q1["question_text"]))

if __name__ == "__main__":
    unittest.main()
