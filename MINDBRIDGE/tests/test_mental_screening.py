"""
Unit & Integration Test Suite for MindBridge Mental Health Screening Engine.
Tests research paper grounding, 100 question generation (50 MCQ, 50 VSAQ),
per-user randomization, voice/text answers, crisis escalation, and non-diagnostic scoring.
"""

import unittest
import os
import sys
import json

# Ensure backend directory is in path
BACKEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import mental_screening as ms
import database as db

class TestMentalScreeningEngine(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        db.init_db()
        cls.engine = ms.MentalScreeningEngine()

    def test_01_research_papers_loading(self):
        """Verify that research papers folder is discovered and clinical instruments are loaded."""
        meta = ms.load_research_papers()
        self.assertIsNotNone(meta)
        self.assertIn("instruments", meta)
        self.assertIn("PHQ-9", meta["instruments"])
        self.assertIn("GAD-7", meta["instruments"])
        self.assertIn("C-SSRS", meta["instruments"])
        self.assertIn("DASS-21", meta["instruments"])
        self.assertIn("WHO-5", meta["instruments"])
        self.assertIn("Saini_et_al_2024", meta["instruments"])
        self.assertGreaterEqual(len(meta["scanned_files"]), 6)

    def test_02_questions_dataset_specifications(self):
        """Verify that questions_100.json meets all required clinical constraints."""
        qs = self.engine.questions
        self.assertEqual(len(qs), 100, f"Expected 100 questions, got {len(qs)}")

        mcqs = [q for q in qs if q["question_type"] == "MCQ"]
        vsaqs = [q for q in qs if q["question_type"] == "VSAQ"]
        safety_qs = [q for q in qs if q.get("is_safety_question") is True]
        phq9_items = [q for q in qs if "phq9_item" in q.get("scoring_rule", "")]
        gad7_items = [q for q in qs if "gad7_item" in q.get("scoring_rule", "")]

        self.assertEqual(len(mcqs), 50, f"Expected exactly 50 MCQs, got {len(mcqs)}")
        self.assertEqual(len(vsaqs), 50, f"Expected exactly 50 VSAQs, got {len(vsaqs)}")
        self.assertGreaterEqual(len(safety_qs), 10, f"Expected at least 10 safety questions, got {len(safety_qs)}")
        self.assertGreaterEqual(len(phq9_items), 9, f"Expected at least 9 PHQ-9 items, got {len(phq9_items)}")
        self.assertGreaterEqual(len(gad7_items), 7, f"Expected at least 7 GAD-7 items, got {len(gad7_items)}")

        # Check that each MCQ has 4 options (A, B, C, D)
        for mcq in mcqs:
            opts = mcq.get("options")
            self.assertIsNotNone(opts, f"MCQ {mcq['question_id']} missing options")
            self.assertEqual(len(opts), 4, f"MCQ {mcq['question_id']} must have exactly 4 options")
            labels = [o["label"] for o in opts]
            self.assertEqual(labels, ["A", "B", "C", "D"])

        # Check required fields for every question
        required_fields = ["question_id", "question_text", "question_type", "domain", "scoring_rule", "is_safety_question", "source_paper"]
        for q in qs:
            for rf in required_fields:
                self.assertIn(rf, q, f"Question {q.get('question_id')} missing required field: {rf}")

    def test_03_per_user_shuffling_randomization(self):
        """Verify that question orders are randomized and different between sessions."""
        user_1_qs = self.engine.shuffle_questions_for_user("user-alice")
        user_2_qs = self.engine.shuffle_questions_for_user("user-bob")

        self.assertEqual(len(user_1_qs), 100)
        self.assertEqual(len(user_2_qs), 100)

        order_1 = [q["question_id"] for q in user_1_qs]
        order_2 = [q["question_id"] for q in user_2_qs]

        # The probability of two 100-item random shuffles being identical is ~ 1 / 100!
        self.assertNotEqual(order_1, order_2, "Two independent sessions should receive different question sequences.")

    def test_04_voice_and_text_recording(self):
        """Verify recording of both voice (with raw transcript) and text answers."""
        sid = db.create_screening_session("user-charlie", ["q1", "q11", "q51"])
        
        # 1. Voice Answer on q1 (MCQ)
        res_voice = self.engine.record_answer(
            session_id=sid,
            user_id="user-charlie",
            question_id="q1",
            answer_text="Several days",
            input_mode="voice",
            raw_transcript="I feel like several days over the last week"
        )
        self.assertEqual(res_voice["status"], "recorded")
        self.assertFalse(res_voice["crisis_detected"])
        self.assertEqual(res_voice["numeric_score"], 1.0)

        # 2. Text Answer on q11 (MCQ)
        res_text = self.engine.record_answer(
            session_id=sid,
            user_id="user-charlie",
            question_id="q11",
            answer_text="Nearly every day",
            input_mode="text"
        )
        self.assertEqual(res_text["status"], "recorded")
        self.assertEqual(res_text["numeric_score"], 3.0)

        # Verify DB answers table
        answers = db.get_session_answers(sid)
        self.assertEqual(len(answers), 2)
        ans_map = {a["question_id"]: a for a in answers}
        self.assertEqual(ans_map["q1"]["input_mode"], "voice")
        self.assertIn("several days", ans_map["q1"]["raw_transcript"].lower())
        self.assertEqual(ans_map["q11"]["input_mode"], "text")

    def test_05_immediate_crisis_escalation(self):
        """Verify that an affirmative answer on acute safety questions immediately halts screening."""
        sid = db.create_screening_session("user-crisis-test", ["q1", "q43", "q4"])
        
        # Normal answer on q1
        r1 = self.engine.record_answer(sid, "user-crisis-test", "q1", "Not at all", input_mode="text")
        self.assertFalse(r1["crisis_detected"])

        # Acute suicidal intent response on safety question q43
        r_crisis = self.engine.record_answer(
            sid,
            "user-crisis-test",
            "q43",
            "Yes, clear intention to act upon them",
            input_mode="voice",
            raw_transcript="Yes, clear intention to act upon them"
        )

        self.assertTrue(r_crisis["crisis_detected"])
        self.assertEqual(r_crisis["status"], "crisis_triggered")
        self.assertEqual(r_crisis["risk_flag"], "immediate")
        self.assertEqual(r_crisis["recommended_action"], "crisis_resources")
        self.assertIn("emergency_resources", r_crisis)
        self.assertIn("Tele-MANAS", str(r_crisis["emergency_resources"]))

        # Verify session is marked crisis_halted in DB
        session = db.get_screening_session(sid)
        self.assertEqual(session["status"], "crisis_halted")
        self.assertEqual(session["crisis_flag"], 1)

    def test_06_non_diagnostic_scoring_and_recommendations(self):
        """Verify scoring bands for PHQ-9, GAD-7, distress indexing, and non-diagnostic constraints."""
        sid = db.create_screening_session("user-eval-test", ["q1", "q2", "q3", "q4", "q5", "q11", "q12", "q13", "q14", "q51", "q52", "q59", "q60", "q61", "q88"])

        # Moderate responses (mix of 1s and 2s)
        answers = {
            "q1": "More than half the days", # PHQ-9 item 1: 2
            "q2": "Several days",           # PHQ-9 item 2: 1
            "q3": "Several days",           # PHQ-9 item 4: 1
            "q4": "Several days",           # PHQ-9 item 6: 1
            "q5": "Several days",           # PHQ-9 item 7: 1
            "q51": "1",                     # PHQ-9 item 5: 1
            "q52": "1",                     # PHQ-9 item 8: 1
            "q88": "0",                     # PHQ-9 item 9 (safety): 0
            "q11": "More than half the days", # GAD-7 item 1: 2
            "q12": "Several days",            # GAD-7 item 2: 1
            "q13": "Several days",            # GAD-7 item 3: 1
            "q14": "Several days",            # GAD-7 item 4: 1
            "q59": "1",                      # GAD-7 item 5: 1
            "q60": "1",                      # GAD-7 item 6: 1
            "q61": "1"                       # GAD-7 item 7: 1
        }

        for qid, ans in answers.items():
            self.engine.record_answer(sid, "user-eval-test", qid, ans, input_mode="text")

        analysis = self.engine.compute_scores_and_analysis(sid)
        
        # Verify PHQ-9 score = 2+1+1+1+1+1+1+0 = 8 (Mild)
        self.assertEqual(analysis["phq9_score"], 8)
        self.assertEqual(analysis["phq9_severity"], "mild")

        # Verify GAD-7 score = 2+1+1+1+1+1+1 = 8 (Mild)
        self.assertEqual(analysis["gad7_score"], 8)
        self.assertEqual(analysis["gad7_severity"], "mild")

        # Verify non-diagnostic rule:
        summary = analysis["summary_text"].lower()
        self.assertNotIn("major depressive disorder", summary)
        self.assertNotIn("generalized anxiety disorder", summary)
        self.assertNotIn("you have depression", summary)
        self.assertNotIn("you have anxiety disorder", summary)

        # Verify disclaimer presence
        self.assertIn("disclaimer", analysis)
        self.assertEqual(analysis["disclaimer"], ms.DISCLAIMER_TEXT)

        # Verify recommended action is psychologist_referral or self_care
        self.assertIn(analysis["recommended_action"], ["psychologist_referral", "self_care"])

    def test_07_patient_intake_simulation_flow(self):
        """
        Simulates a full user intake answering 12 questions in random order,
        demonstrating voice transcript review and deterministic safety handling.
        """
        sim_user = "sim-patient-007"
        shuffled = self.engine.shuffle_questions_for_user(sim_user)
        sid = db.create_screening_session(sim_user, [q["question_id"] for q in shuffled])

        answered_count = 0
        safety_asked = False

        for q in shuffled[:14]:
            qid = q["question_id"]
            if q.get("is_safety_question"):
                # Answer negative on safety to test non-crisis path
                ans_text = "No, never had this wish" if q["question_type"] == "MCQ" else "No"
                safety_asked = True
            elif q["question_type"] == "MCQ":
                ans_text = q["options"][1]["text"] # Moderate score 1
            else:
                ans_text = "1"
            
            res = self.engine.record_answer(
                session_id=sid,
                user_id=sim_user,
                question_id=qid,
                answer_text=ans_text,
                input_mode="voice",
                raw_transcript=f"I would say {ans_text}"
            )
            answered_count += 1
            self.assertFalse(res["crisis_detected"])

        self.assertEqual(answered_count, 14)
        
        # Test evaluating session in progress
        eval_result = self.engine.compute_scores_and_analysis(sid)
        self.assertIn("overall_distress", eval_result)
        self.assertIn("recommended_action", eval_result)
        self.assertIn("summary_text", eval_result)
        print(f"\n[Simulation Intake Result Summary]: {eval_result['summary_text'][:120]}...")
        print(f"[Recommended Action]: {eval_result['recommended_action']}")

if __name__ == "__main__":
    unittest.main()
