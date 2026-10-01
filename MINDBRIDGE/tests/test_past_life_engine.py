"""
Automated Unit and Integration Tests for MindBridge Past Life Reflection Engine.
Tests intent detection, question progression, multilingual support (EN, HI, BN),
voice/text answer handling, and post-interview Mental State evaluation.
"""

import os
import sys
import unittest

# Ensure backend directory is in path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from past_life_engine import past_life_engine  # type: ignore[import-not-found]
import database as db  # type: ignore[import-not-found]
from server import app  # type: ignore[import-not-found]

class TestPastLifeEngine(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        db.init_db()

    def test_01_trigger_intent_detection(self):
        """Verify natural language trigger detection across English, Hindi, Hinglish, and Bengali."""
        # English
        self.assertEqual(past_life_engine.detect_trigger_intent("I want to talk about my past life"), "en")
        self.assertEqual(past_life_engine.detect_trigger_intent("Can we reflect on my childhood memories?"), "en")
        self.assertEqual(past_life_engine.detect_trigger_intent("I have unresolved past hurts"), "en")

        # Bengali
        self.assertEqual(past_life_engine.detect_trigger_intent("আমি আমার অতীতের কথা বলতে চাই"), "bn")
        self.assertEqual(past_life_engine.detect_trigger_intent("ছোটবেলার স্মৃতি নিয়ে কিছু ভাবছি"), "bn")
        self.assertEqual(past_life_engine.detect_trigger_intent("অতীতের প্রশ্নগুলোর উত্তর দিতে চাই"), "bn")

        # Hindi & Hinglish
        self.assertEqual(past_life_engine.detect_trigger_intent("मैं अपने अतीत के बारे में बात करना चाहता हूँ"), "hi")
        self.assertEqual(past_life_engine.detect_trigger_intent("बचपन की यादें याद आ रही हैं"), "hi")
        self.assertEqual(past_life_engine.detect_trigger_intent("mujhe apne past ke baare mein baat karni hai"), "hi")

        # Non-trigger inputs
        self.assertIsNone(past_life_engine.detect_trigger_intent("What is the weather today?"))
        self.assertIsNone(past_life_engine.detect_trigger_intent("Hello, how are you?"))

    def test_02_question_sets_and_modes(self):
        """Verify full 13 questions and short 6-question interview sequences exist with all 3 languages."""
        short_qs = past_life_engine.get_question_sequence("short")
        full_qs = past_life_engine.get_question_sequence("full")

        self.assertEqual(len(short_qs), 6)
        self.assertEqual(len(full_qs), 13)

        for q in full_qs:
            self.assertIn("en", q["question_text"])
            self.assertIn("bn", q["question_text"])
            self.assertIn("hi", q["question_text"])
            self.assertIn("en", q["gentle_support"])
            self.assertIn("bn", q["gentle_support"])
            self.assertIn("hi", q["gentle_support"])
            self.assertIn("en", q["suggested_chips"])
            self.assertIn("bn", q["suggested_chips"])
            self.assertIn("hi", q["suggested_chips"])

    def test_03_interview_flow_english(self):
        """Verify complete short interview flow in English with final mental state analysis."""
        user_id = "test_user_en"
        conv_id = "conv_test_en"

        # Start session
        start_res = past_life_engine.start_session(user_id, conv_id, language="en", mode="short")
        session_id = start_res["session_id"]
        self.assertIsNotNone(session_id)
        self.assertEqual(start_res["total_questions"], 6)
        self.assertEqual(start_res["current_index"], 0)
        self.assertIn("MindBridge Life Reflection Sanctuary", start_res["formatted_message"])

        # Answer Q1 (Boundary Check)
        ans1 = past_life_engine.process_answer(session_id, "I feel comfortable sharing some parts of my childhood.", is_audio=False)
        self.assertFalse(ans1["is_complete"])
        self.assertEqual(ans1["current_index"], 1)

        # Answer Q2 (Happiest memories)
        ans2 = past_life_engine.process_answer(session_id, "Playing outside in the rain with my brother was pure joy.", is_audio=True, input_mode="voice")
        self.assertFalse(ans2["is_complete"])
        self.assertEqual(ans2["current_index"], 2)

        # Answer Q3 (Turning Point)
        ans3 = past_life_engine.process_answer(session_id, "Moving to college made me independent and resilient.", is_audio=False)
        self.assertFalse(ans3["is_complete"])
        self.assertEqual(ans3["current_index"], 3)

        # Answer Q4 (Carrying difficult experiences)
        ans4 = past_life_engine.process_answer(session_id, "I went through some lonely years, but I've learned to set boundaries.", is_audio=False)
        self.assertFalse(ans4["is_complete"])
        self.assertEqual(ans4["current_index"], 4)

        # Answer Q5 (Unresolved Experiences)
        ans5 = past_life_engine.process_answer(session_id, "I am learning to forgive past mistakes and find peace.", is_audio=False)
        self.assertFalse(ans5["is_complete"])
        self.assertEqual(ans5["current_index"], 5)

        # Answer Q6 (Relational Trust - Final Question)
        ans6 = past_life_engine.process_answer(session_id, "Past heartbreak taught me to value genuine, safe bonds.", is_audio=True, input_mode="voice")
        self.assertTrue(ans6["is_complete"])
        self.assertIn("analysis", ans6)
        
        analysis = ans6["analysis"]
        self.assertGreaterEqual(analysis["nostalgia_index"], 0)
        self.assertGreaterEqual(analysis["resilience_index"], 0)
        self.assertGreaterEqual(analysis["trust_index"], 0)
        self.assertIn("Life Reflection & Mental State Synthesis", analysis["narrative_report"])

    def test_04_interview_flow_bengali(self):
        """Verify Bengali life reflection interview with authentic Bengali output and mental state evaluation."""
        user_id = "test_user_bn"
        conv_id = "conv_test_bn"

        start_res = past_life_engine.start_session(user_id, conv_id, language="bn", mode="short")
        session_id = start_res["session_id"]
        self.assertIn("স্মৃতি অনুধ্যান", start_res["formatted_message"])

        # Answer 6 Bengali questions
        sample_answers = [
            "আমি কথা বলতে স্বাচ্ছন্দ্য বোধ করছি।",
            "ছোটবেলায় বন্ধুদের সাথে বৃষ্টির দিনে ফুটবল খেলার স্মৃতি খুব আনন্দের ছিল।",
            "কলেজে আসার পর আমার জীবন দেখার দৃষ্টিভঙ্গি বদলে যায় এবং আমি অনেক স্বাবলম্বী হয়েছি।",
            "কঠিন পরিস্থিতি অনেক কষ্ট দিয়েছে কিন্তু আমি ধৈর্য ধরতে শিখেছি।",
            "কিছু না-বলা কথা হয়তো আছে, তবে আস্তে আস্তে মন হালকা করতে শিখেছি।",
            "অতীতের সম্পর্কগুলো আমাকে খাঁটি মানুষের মূল্য বুঝতে শিখিয়েছে।"
        ]

        for i, ans_text in enumerate(sample_answers):
            res = past_life_engine.process_answer(session_id, ans_text, is_audio=(i % 2 == 1))
            if i == 5:
                self.assertTrue(res["is_complete"])
                self.assertIn("মানসিক অবস্থা বিশ্লেষণ", res["analysis"]["narrative_report"])
            else:
                self.assertFalse(res["is_complete"])

    def test_05_interview_flow_hindi(self):
        """Verify Hindi life reflection interview with authentic Hindi output and mental state evaluation."""
        user_id = "test_user_hi"
        conv_id = "conv_test_hi"

        start_res = past_life_engine.start_session(user_id, conv_id, language="hi", mode="short")
        session_id = start_res["session_id"]
        self.assertIn("अतीत संस्मरण", start_res["formatted_message"])

        sample_answers = [
            "हाँ, मैं खुलकर बात करने के लिए तैयार हूँ।",
            "बचपन में माँ के हाथ की खीर और त्योहारों का उत्साह सबसे प्यारी याद है।",
            "जब मैंने पहली नौकरी शुरू की तो मुझे अपनी हिम्मत और समझदारी का अहसास हुआ।",
            "मुश्किल दिनों ने मुझे धैर्य और अंदरूनी ताकत सिखाई है।",
            "पुरानी गलतियों को भुलाकर अब मैं खुद को माफ करना सीख रहा हूँ।",
            "अतीत के खट्टे-मीठे अनुभवों ने मुझे सच्चे और ईमानदार रिश्तों की कद्र करना सिखाया।"
        ]

        for i, ans_text in enumerate(sample_answers):
            res = past_life_engine.process_answer(session_id, ans_text)
            if i == 5:
                self.assertTrue(res["is_complete"])
                self.assertIn("मानसिक स्थिति विश्लेषण", res["analysis"]["narrative_report"])
            else:
                self.assertFalse(res["is_complete"])

    def test_06_chat_endpoint_integration(self):
        """Verify /api/chat auto-triggers past life interview when user mentions past life query."""
        # 1. Trigger via English text in /api/chat
        res = self.app.post("/api/chat", json={
            "message": "I want to talk about my past life and childhood memories",
            "user_id": "api_test_user",
            "language": "en-US"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("past_life_active"))
        self.assertIsNotNone(data.get("past_life_session"))
        session_id = data["past_life_session"]["session_id"]

        # 2. Answer through /api/chat with past_life_session_id
        res2 = self.app.post("/api/chat", json={
            "message": "I am open to talking about my early years",
            "user_id": "api_test_user",
            "past_life_session_id": session_id
        })
        self.assertEqual(res2.status_code, 200)
        data2 = res2.get_json()
        self.assertTrue(data2.get("past_life_active"))
        self.assertFalse(data2.get("past_life_completed"))

    def test_07_rest_endpoints(self):
        """Verify /api/past-life/* REST endpoints."""
        # GET questions
        q_res = self.app.get("/api/past-life/questions?mode=short")
        self.assertEqual(q_res.status_code, 200)
        self.assertEqual(q_res.get_json()["total"], 6)

        # POST start
        start_res = self.app.post("/api/past-life/start", json={
            "user_id": "rest_tester",
            "language": "bn",
            "mode": "short"
        })
        self.assertEqual(start_res.status_code, 200)
        s_data = start_res.get_json()["session"]
        sid = s_data["session_id"]

        # POST answer
        ans_res = self.app.post("/api/past-life/answer", json={
            "session_id": sid,
            "user_id": "rest_tester",
            "answer": "আমি সহজ বোধ করছি",
            "is_audio": False
        })
        self.assertEqual(ans_res.status_code, 200)
        self.assertFalse(ans_res.get_json()["result"]["is_complete"])

        # GET session status
        status_res = self.app.get(f"/api/past-life/session/{sid}")
        self.assertEqual(status_res.status_code, 200)


if __name__ == "__main__":
    unittest.main()
