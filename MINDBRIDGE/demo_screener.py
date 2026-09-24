"""
MindBridge Clinical Screener Simulation Demo.
Demonstrates the research-grounded 100-question screening flow:
1. Grounded in research papers: PHQ-9, GAD-7, DASS-21, WHO-5, C-SSRS, and Saini et al. (2024).
2. Per-user question shuffling.
3. Dual-input simulation: Voice (preferred with raw transcript) and Text.
4. Immediate Crisis Interception on safety questions.
5. Non-diagnostic psychometric distress scoring and tiered care recommendations.
"""

import os
import sys
import json
import time

# Ensure backend path is accessible
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import mental_screening as ms
import database as db

def run_research_screener_simulation(scenario_name: str, user_id: str, responses: list):
    db.init_db()
    engine = ms.MentalScreeningEngine()
    
    print("=" * 80)
    print(f"  SCENARIO: {scenario_name}")
    print("=" * 80)
    print(f"  User ID: {user_id}")
    print(f"  Disclaimer: {ms.DISCLAIMER_TEXT}\n")

    # 1. Shuffling questions for this user session
    shuffled_qs = engine.shuffle_questions_for_user(user_id)
    order_ids = [q["question_id"] for q in shuffled_qs]
    session_id = db.create_screening_session(user_id, order_ids)
    print(f"  Session Created: {session_id}")
    print(f"  100 Questions Shuffled specifically for {user_id}.")
    print(f"  First 5 shuffled questions: {order_ids[:5]}\n")

    crisis_triggered = False

    # 2. Iterate through simulated responses
    for i, resp in enumerate(responses):
        qid = resp["question_id"]
        q = engine.get_question(qid)
        if not q:
            continue

        q_type = q["question_type"]
        is_safe = q.get("is_safety_question", False)
        mode = resp.get("input_mode", "voice")
        ans_text = resp["answer_text"]
        raw_tr = resp.get("raw_transcript", ans_text)

        safe_indicator = " [SAFETY QUESTION]" if is_safe else ""
        print(f"Question {i+1} [{q['domain'].upper()} | {q_type}]{safe_indicator}:")
        print(f"  MindBridge: \"{q['question_text']}\"")
        if q_type == "MCQ":
            opts_str = ", ".join(["(" + o["label"] + ") " + o["text"] for o in q.get("options", [])])
            print(f"    Options: {opts_str}")
        print(f"  --> User Response ({mode.upper()}): \"{ans_text}\"")
        if mode == "voice":
            print(f"      [Captured Raw Audio Transcript]: \"{raw_tr}\"")

        # Record answer
        rec_res = engine.record_answer(
            session_id=session_id,
            user_id=user_id,
            question_id=qid,
            answer_text=ans_text,
            input_mode=mode,
            raw_transcript=raw_tr
        )

        if rec_res.get("crisis_detected"):
            crisis_triggered = True
            print("\n" + "!" * 80)
            print("  *** IMMEDIATE CRISIS INTERCEPTION TRIGGERED ***")
            print("  Normal screening question flow has been HALTED immediately.")
            print(f"  Reason: {rec_res.get('reason')}")
            print(f"  Recommended Action: {rec_res.get('recommended_action').upper()}")
            print(f"  Crisis Resources Provided:")
            for res_item in rec_res["emergency_resources"]["india"]:
                print(f"    - {res_item['name']}: {res_item['number']} ({res_item['hours']})")
            print("!" * 80 + "\n")
            break

        print(f"      [Score Recorded]: {rec_res.get('numeric_score')} | Next Q Index: {rec_res.get('current_index')}\n")

    # 3. Compute final scores and mental-state analysis
    analysis = engine.compute_scores_and_analysis(session_id)

    print("-" * 80)
    print("  FINAL EVALUATION OUTPUT (Canonical JSON Schema):")
    print("-" * 80)
    print(json.dumps(analysis, indent=2))
    print("-" * 80)
    print(f"  Overall Distress: {analysis['overall_distress'].upper()} | Risk Flag: {analysis['risk_flag'].upper()}")
    print(f"  Recommended Action: {analysis['recommended_action'].upper()}")
    print(f"  Summary Text: {analysis['summary_text']}")
    print("=" * 80 + "\n")
    return analysis

def main():
    # Scenario A: Moderate Distress (Stress, Sleep fragmentation, Mild anxiety - Voice-First Intake)
    scenario_a_responses = [
        {"question_id": "q1", "answer_text": "Several days", "input_mode": "voice", "raw_transcript": "I felt that way several days over the last two weeks"},
        {"question_id": "q2", "answer_text": "Several days", "input_mode": "voice", "raw_transcript": "Down several days"},
        {"question_id": "q11", "answer_text": "More than half the days", "input_mode": "voice", "raw_transcript": "Felt nervous more than half the days"},
        {"question_id": "q12", "answer_text": "Several days", "input_mode": "text"},
        {"question_id": "q19", "answer_text": "Applied to a considerable degree / often", "input_mode": "voice", "raw_transcript": "Hard to wind down after work often"},
        {"question_id": "q27", "answer_text": "More than half the days", "input_mode": "voice", "raw_transcript": "Trouble falling asleep more than half the days"},
        {"question_id": "q29", "answer_text": "45 to 90 minutes (moderate insomnia)", "input_mode": "text"},
        {"question_id": "q34", "answer_text": "Somewhat difficult", "input_mode": "text"},
        {"question_id": "q40", "answer_text": "No, never had this wish", "input_mode": "voice", "raw_transcript": "No never had this wish at all"},
        {"question_id": "q46", "answer_text": "Somewhat supported by one or two people", "input_mode": "voice", "raw_transcript": "I feel supported by one or two close friends"},
        {"question_id": "q48", "answer_text": "Open if given clear, confidential support", "input_mode": "text"},
        {"question_id": "q75", "answer_text": "5.5", "input_mode": "voice", "raw_transcript": "About five and a half hours"},
        {"question_id": "q88", "answer_text": "Not at all", "input_mode": "voice", "raw_transcript": "Not at all zero"}
    ]

    # Scenario B: Acute Safety Concern (Suicidal Intent & Plan - Immediate Escalation)
    scenario_b_responses = [
        {"question_id": "q1", "answer_text": "Nearly every day", "input_mode": "voice", "raw_transcript": "Nearly every day I have no pleasure"},
        {"question_id": "q2", "answer_text": "Nearly every day", "input_mode": "voice", "raw_transcript": "Depressed nearly every day"},
        {"question_id": "q43", "answer_text": "Yes, clear intention to act upon them", "input_mode": "voice", "raw_transcript": "Yes I have clear intention to act upon these thoughts"},
        {"question_id": "q4", "answer_text": "Nearly every day", "input_mode": "text"} # Should not be reached!
    ]

    run_research_screener_simulation(
        "Scenario 1: Moderate Distress & Sleep Strain (Psychologist Referral)",
        "patient-maya-voice",
        scenario_a_responses
    )

    run_research_screener_simulation(
        "Scenario 2: Acute Safety Trigger (Immediate Crisis Interception & Halting)",
        "patient-crisis-flow",
        scenario_b_responses
    )

if __name__ == "__main__":
    main()

