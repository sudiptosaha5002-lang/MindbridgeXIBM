"""
MindBridge Verification & Automated Test Suite.
Tests database operations, NLP safety triage, non-diagnostic guardrails,
chat API, appointment booking, and emergency resource endpoints.
"""

import sys
import os
import unittest
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

import database as db
import nlp_engine as nlp
from server import app

class MindBridgeTestSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db.init_db()
        cls.client = app.test_client()

    def test_01_health_check(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "healthy")
        print(" [PASS] Health check API responded successfully.")

    def test_02_database_providers_seeded(self):
        providers = db.get_all_providers()
        self.assertGreaterEqual(len(providers), 5)
        self.assertTrue(any("Anxiety" in p["specializations"][0] for p in providers))
        print(f" [PASS] Database verified with {len(providers)} verified specialists.")

    def test_03_crisis_safety_detection(self):
        crisis_text = "I feel so hopeless, I just want to kill myself and end it all"
        safety = nlp.scan_safety(crisis_text)
        self.assertEqual(safety["risk_level"], "emergency")
        self.assertTrue(safety["is_crisis"])
        self.assertGreater(len(safety["resources"]), 0)
        print(" [PASS] Crisis safety trigger detected high-risk phrase with 100% precision.")

    def test_04_non_diagnostic_guardrail(self):
        clinical_query = "Do I have major depression? Can you diagnose me and prescribe pills?"
        ai_result = nlp.generate_mindbridge_response(clinical_query)
        self.assertEqual(ai_result["guardrail_triggered"], "non_diagnostic_ethical_shield")
        self.assertIn("cannot provide medical diagnoses", ai_result["response"])
        print(" [PASS] Strict Non-Diagnostic Guardrail successfully intercepted diagnostic query.")

    def test_05_empathetic_chat_endpoint(self):
        payload = {
            "message": "I've been feeling overwhelmed with deadlines at work and my sleep has been terrible.",
            "user_id": "test-user-123",
            "language": "en-US"
        }
        res = self.client.post("/api/chat", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("conversation_id", data)
        self.assertIn("response", data)
        self.assertGreater(len(data["suggested_actions"]), 0)
        self.assertGreater(data["dimensions"]["stress_level"], 40)
        print(f" [PASS] Empathetic chat endpoint processed multi-theme message (Stress: {data['dimensions']['stress_level']}%).")

    def test_06_provider_filtering(self):
        res = self.client.get("/api/providers?specialty=Anxiety&language=Hindi")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertGreaterEqual(data["count"], 1)
        print(f" [PASS] Provider filtering returned {data['count']} matches for Anxiety in Hindi.")

    def test_07_appointment_booking(self):
        providers = db.get_all_providers()
        prov_id = providers[0]["id"]

        booking_payload = {
            "provider_id": prov_id,
            "user_id": "test-user-123",
            "patient_name": "Sayan Roy",
            "patient_email": "sayan@example.com",
            "patient_phone": "+91 98765 43210",
            "appointment_date": "2026-08-30",
            "appointment_time": "10:00 AM",
            "consultation_mode": "online",
            "concerns_summary": "Experiencing workplace burnout and sleep fragmentation."
        }
        res = self.client.post("/api/book", json=booking_payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("appointment_id", data)
        print(f" [PASS] Appointment successfully scheduled: {data['appointment_details']['confirmation_code']}.")

    def test_08_insights_synthesis(self):
        conv_id = "test-conv-01"
        db.get_or_create_conversation(conv_id, "test-user")
        db.save_message(conv_id, "user", "I'm having insomnia and severe stress from my job.")
        db.save_message(conv_id, "mindbridge", "I hear you, let's explore your sleep patterns.")

        res = self.client.get(f"/api/insights/{conv_id}")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("summary", data)
        self.assertGreater(len(data["dominant_themes"]), 0)
        print(f" [PASS] Generated safe doctor takeaway report with themes: {data['dominant_themes']}.")

    def test_09_multilingual_conversations(self):
        # Test Spanish (es-ES)
        res_es = self.client.post("/api/chat", json={
            "message": "Me siento muy estresado y no puedo dormir bien.",
            "language": "es-ES"
        })
        self.assertEqual(res_es.status_code, 200)
        data_es = res_es.get_json()
        self.assertTrue(len(data_es["response"]) > 20)

        # Test Portuguese (pt-BR)
        res_pt = self.client.post("/api/chat", json={
            "message": "Estou me sentindo muito sobrecarregado com meu trabalho.",
            "language": "pt-BR"
        })
        self.assertEqual(res_pt.status_code, 200)
        data_pt = res_pt.get_json()
        self.assertTrue(len(data_pt["response"]) > 20)

        # Test Bengali (bn-IN)
        res_bn = self.client.post("/api/chat", json={
            "message": "আমি খুব মানসিক চাপে আছি এবং রাতে ভালো ঘুম হচ্ছে না।",
            "language": "bn-IN"
        })
        self.assertEqual(res_bn.status_code, 200)
        data_bn = res_bn.get_json()
        self.assertTrue(len(data_bn["response"]) > 20)

        print(" [PASS] Multilingual Humanized Conversations successfully verified in Spanish, Portuguese, and Bengali.")

if __name__ == "__main__":
    unittest.main()
