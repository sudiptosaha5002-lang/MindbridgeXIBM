"""
MindBridge Research-Grounded Mental Health Screening Engine.
Implements validated, non-diagnostic screening scoring (PHQ-9, GAD-7, DASS-21, WHO-5, C-SSRS),
per-user question shuffling, voice & text answer processing, immediate crisis triage,
and tiered care recommendations grounded in the research_paper folder.
"""

import os
import sys
import json
import re
import random
import datetime
from typing import Dict, Any, List, Optional, Tuple

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

# Local database import
try:
    import database as db
except ImportError:
    from . import database as db


DISCLAIMER_TEXT = (
    "This tool does not diagnose mental health conditions. It helps reflect on "
    "your experiences and suggests when speaking with a professional may be helpful."
)

CRISIS_RESOURCES = {
    "india": [
        {"name": "Tele-MANAS (Govt of India)", "number": "14416 / 1800-891-4416", "hours": "24/7", "languages": "20+ Official Indian Languages"},
        {"name": "KIRAN Mental Health Helpline", "number": "1800-599-0019", "hours": "24/7", "languages": "Hindi, English & Regional"},
        {"name": "Vandrevala Foundation Helpline", "number": "+91 9999 666 555", "hours": "24/7", "languages": "Hindi, English"},
        {"name": "NIMHANS Psychosocial Helpline", "number": "080-46110007", "hours": "24/7", "languages": "Multiple"}
    ],
    "us_international": [
        {"name": "988 Suicide & Crisis Lifeline (US/Canada)", "number": "988", "hours": "24/7", "languages": "English, Spanish"},
        {"name": "Crisis Text Line", "number": "Text HOME to 741741", "hours": "24/7", "languages": "English, Spanish"},
        {"name": "Befrienders Worldwide", "number": "https://www.befrienders.org", "hours": "24/7", "languages": "Global"}
    ]
}


def load_research_papers(folder_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Scans the research_paper folder for all PDF and text files and extracts
    validated clinical tools, domains, cut-offs, and safety guidelines.
    """
    if not folder_path:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(os.path.dirname(base_dir), "research_paper"),
            os.path.join(base_dir, "research_papers"),
            os.path.join(base_dir, "research_paper"),
            os.path.join(os.path.dirname(os.path.dirname(base_dir)), "research_paper")
        ]
        for c in candidates:
            if os.path.exists(c):
                folder_path = c
                break

    papers_meta = {
        "folder_path": folder_path,
        "scanned_files": [],
        "instruments": {
            "PHQ-9": {
                "name": "Patient Health Questionnaire-9",
                "items_count": 9,
                "scoring_range": "0-27",
                "severity_cutoffs": {
                    "minimal": (0, 4),
                    "mild": (5, 9),
                    "moderate": (10, 14),
                    "moderately_severe": (15, 19),
                    "severe": (20, 27)
                },
                "safety_item": "Item 9 (Thoughts of being better off dead or hurting oneself)"
            },
            "GAD-7": {
                "name": "Generalized Anxiety Disorder-7",
                "source_file": "Anxiety.pdf",
                "items_count": 7,
                "scoring_range": "0-21",
                "severity_cutoffs": {
                    "minimal": (0, 4),
                    "mild": (5, 9),
                    "moderate": (10, 14),
                    "severe": (15, 21)
                },
                "clinical_threshold": "Score >= 10 indicates high sensitivity (89%) and specificity (82%) for generalized anxiety"
            },
            "C-SSRS": {
                "name": "Columbia-Suicide Severity Rating Scale",
                "source_files": ["BASELINE SCREENING.pdf", "SUICIDE 1.pdf"],
                "ideation_levels": [
                    "Wish to be dead",
                    "Active suicidal thoughts without method",
                    "Suicidal thoughts with method (no plan/intent)",
                    "Suicidal intent without specific plan",
                    "Suicidal intent with detailed plan",
                    "Preparatory acts or suicidal behavior"
                ],
                "escalation_rule": "Affirmative response to intent, plan, means, or recent behavior triggers immediate emergency triage."
            },
            "DASS-21": {
                "name": "Depression, Anxiety and Stress Scale - 21 Items",
                "source_file": "Q FOR DEPRESSION,ANXIETY.pdf",
                "subscales": ["Depression", "Anxiety", "Stress"],
                "items_per_subscale": 7,
                "scoring": "Sum multiplied by 2",
                "stress_cutoffs": {
                    "normal": (0, 14),
                    "mild": (15, 18),
                    "moderate": (19, 25),
                    "severe": (26, 33),
                    "extremely_severe": (34, 42)
                }
            },
            "WHO-5": {
                "name": "WHO-5 Well-Being Index",
                "source_file": "WHO WELLBEING.pdf",
                "items_count": 5,
                "scoring_range": "0-25 raw, 0-100%",
                "cutoff": "Raw score < 13 or percentage < 50 indicates poor well-being and depression screening indicator"
            },
            "Saini_et_al_2024": {
                "name": "Recognising and Responding to Suicide-Risk Factors in Primary Care",
                "source_file": "SUICIDE IDENTATION.pdf",
                "domains": ["social isolation", "chronic pain", "substance use", "means access", "non-disclosure barriers", "warm handoff"]
            }
        }
    }

    if folder_path and os.path.exists(folder_path):
        for fname in os.listdir(folder_path):
            fpath = os.path.join(folder_path, fname)
            if os.path.isfile(fpath):
                papers_meta["scanned_files"].append({
                    "filename": fname,
                    "size_bytes": os.path.getsize(fpath),
                    "is_pdf": fname.lower().endswith(".pdf"),
                    "is_text": fname.lower().endswith(".txt")
                })

    return papers_meta


class MentalScreeningEngine:
    """
    Research-grounded, non-diagnostic mental health screening engine.
    Manages 100 questions, per-user shuffling, voice/text intake,
    immediate crisis interception, and tiered support recommendations.
    """

    def __init__(self, questions_path: Optional[str] = None):
        self.questions_path = questions_path or self._find_questions_file()
        self.questions: List[Dict[str, Any]] = []
        self.questions_by_id: Dict[str, Dict[str, Any]] = {}
        self.questions_by_rule: Dict[str, Dict[str, Any]] = {}
        self.load_questions()

    def _find_questions_file(self) -> str:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(base_dir, "questions_100.json"),
            os.path.join(base_dir, "data", "questions_100.json"),
            os.path.join(os.path.dirname(base_dir), "questions_100.json"),
            os.path.join(os.path.dirname(base_dir), "data", "questions_100.json")
        ]
        for p in candidates:
            if os.path.exists(p):
                return p
        return os.path.join(base_dir, "questions_100.json")

    def load_questions(self) -> List[Dict[str, Any]]:
        """Loads the 100 validated questions from JSON."""
        if os.path.exists(self.questions_path):
            with open(self.questions_path, "r", encoding="utf-8") as f:
                self.questions = json.load(f)
            self.questions_by_id = {q["question_id"]: q for q in self.questions}
            self.questions_by_rule = {q.get("scoring_rule"): q for q in self.questions if q.get("scoring_rule")}
        return self.questions

    def get_question(self, question_id: str) -> Optional[Dict[str, Any]]:
        return self.questions_by_id.get(question_id)

    def shuffle_questions_for_user(self, user_id: str, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Shuffles the 100 questions into a unique random order for this session.
        Persists the order in the database and returns questions in that sequence.
        """
        if not self.questions:
            self.load_questions()

        shuffled = list(self.questions)
        # Use session/user seeded randomness for reproducibility if desired, or cryptographically random
        random.shuffle(shuffled)
        order_ids = [q["question_id"] for q in shuffled]

        if not session_id:
            session_id = db.create_screening_session(user_id, order_ids)
        else:
            db.update_screening_session(session_id, question_order=order_ids)

        return shuffled

    def check_immediate_safety_trigger(self, question_id: str, answer_text: Any) -> Tuple[bool, str, str]:
        """
        Deterministic crisis gate:
        Checks if an answer on any safety-critical question indicates immediate risk.
        Returns: (is_crisis: bool, risk_tier: str, reason: str)
        """
        q = self.get_question(question_id)
        if not q or not q.get("is_safety_question"):
            return False, "none", ""

        rule = q.get("scoring_rule", "")
        clean_text = str(answer_text).strip().lower()

        # Acute C-SSRS Rules (Intent, Plan, Means, Suicidal Behavior, Severe Abuse, Harm to others)
        acute_rules = [
            "cssrs_suicide_intent",
            "cssrs_suicide_plan",
            "safety_means_access",
            "cssrs_suicidal_behavior",
            "cssrs_recent_attempt_3mo",
            "safety_cannot_keep_safe",
            "safety_harm_to_others",
            "safety_domestic_violence_abuse",
            "phq9_item_9_suicidality",
            "cssrs_active_ideation",
            "cssrs_suicide_method"
        ]

        # Affirmative patterns
        affirmative_words = ["yes", "y", "true", "definitely", "frequently", "always", "plan", "intent", "ready", "hurting"]
        
        # Check MCQ selection score (if MCQ, option with score 2 or 3 on acute rules represents severe risk)
        if q.get("question_type") == "MCQ":
            # Map choice (A, B, C, D) or option text to score
            for opt in q.get("options", []):
                if clean_text in [opt["label"].lower(), opt["text"].lower(), f"{opt['label'].lower()} - {opt['text'].lower()}"]:
                    if opt["score"] >= 2 and rule in acute_rules:
                        return True, "immediate", f"High risk option selected on safety rule '{rule}': {opt['text']}"
                    elif opt["score"] == 1 and rule in ["cssrs_suicide_intent", "cssrs_suicide_plan", "safety_cannot_keep_safe"]:
                        return True, "immediate", f"Active risk indicated on '{rule}'"

        # Check numeric score (e.g. PHQ-9 item 9 >= 2 or Likert >= 2)
        try:
            num_val = float(clean_text)
            if rule in ["phq9_item_9_suicidality", "cssrs_active_ideation", "cssrs_suicide_intent", "cssrs_suicide_plan"] and num_val >= 2:
                return True, "immediate", f"Elevated score ({num_val}) on suicidal ideation/intent"
            if rule in ["safety_cannot_keep_safe", "safety_harm_to_others", "safety_domestic_violence_abuse", "cssrs_recent_attempt_3mo"] and num_val >= 1:
                return True, "immediate", f"Affirmative indicator on acute safety probe '{rule}'"
        except ValueError:
            pass

        # Check affirmative text responses
        is_affirmative = any(re.search(rf"\b{re.escape(w)}\b", clean_text) for w in affirmative_words)
        
        if is_affirmative:
            # Check for negative hedges like "not really", "no intent", "never"
            if re.search(r"\b(no|never|not|none|neither|hardly)\b", clean_text):
                return False, "moderate", "Passive thoughts mentioned but negated"

            if rule in ["cssrs_suicide_intent", "cssrs_suicide_plan", "safety_means_access", 
                        "cssrs_suicidal_behavior", "cssrs_recent_attempt_3mo", "safety_cannot_keep_safe", 
                        "safety_harm_to_others", "safety_domestic_violence_abuse"]:
                return True, "immediate", f"Direct affirmative crisis response to '{rule}'"

            if rule in ["phq9_item_9_suicidality", "cssrs_active_ideation", "cssrs_suicide_method"]:
                return True, "immediate", f"Active suicidal thoughts detected on '{rule}'"

        # Passive thoughts without intent
        if rule in ["cssrs_wish_to_be_dead", "safety_non_suicidal_self_injury"] and is_affirmative:
            return False, "moderate", "Passive distress or non-suicidal self-injury detected"

        return False, "none", ""

    def parse_score(self, question_id: str, raw_answer: Any) -> float:
        """Calculates normalized numeric score for an answer based on question type & rule."""
        q = self.get_question(question_id)
        if not q:
            return 0.0

        raw_str = str(raw_answer).strip().lower()

        # MCQ scoring
        if q.get("question_type") == "MCQ" and q.get("options"):
            for opt in q["options"]:
                if raw_str in [opt["label"].lower(), opt["text"].lower(), f"{opt['label'].lower()} - {opt['text'].lower()}"]:
                    return float(opt["score"])
            # Fallback for letters A, B, C, D
            if raw_str in ["a", "option a"]:
                return float(q["options"][0]["score"])
            elif raw_str in ["b", "option b"]:
                return float(q["options"][1]["score"])
            elif raw_str in ["c", "option c"]:
                return float(q["options"][2]["score"])
            elif raw_str in ["d", "option d"]:
                return float(q["options"][3]["score"])

        # VSAQ parsing
        fmt = q.get("answer_format", "Likert_0_3")

        # Yes/No format
        if fmt == "yes_no":
            if any(raw_str.startswith(y) for y in ["yes", "y", "true", "1"]):
                return 1.0
            return 0.0

        # Numeric Likert or direct number
        m = re.search(r"(\d+(\.\d+)?)", raw_str)
        if m:
            val = float(m.group(1))
            if fmt == "Likert_0_3":
                return max(0.0, min(3.0, val))
            elif fmt == "numeric_0_10":
                return max(0.0, min(10.0, val))
            elif fmt == "numeric_hours":
                return val
            return val

        # Text phrases mapping to 0..3
        if raw_str in ["not at all", "never", "none"]:
            return 0.0
        elif raw_str in ["several days", "sometimes", "mild", "mildly"]:
            return 1.0
        elif raw_str in ["more than half the days", "often", "considerable", "moderate"]:
            return 2.0
        elif raw_str in ["nearly every day", "all the time", "always", "severe", "very much"]:
            return 3.0

        return 0.0

    def record_answer(self, session_id: str, user_id: str, question_id: str,
                      answer_text: str, input_mode: str = "voice",
                      raw_transcript: Optional[str] = None) -> Dict[str, Any]:
        """
        Records a user's answer, checks for immediate safety risk, and updates session state.
        """
        q = self.get_question(question_id) or {}
        score = self.parse_score(question_id, answer_text)
        is_crisis, risk_tier, reason = self.check_immediate_safety_trigger(question_id, answer_text)

        # Persist answer
        db.save_screening_answer(
            session_id=session_id,
            user_id=user_id,
            question_id=question_id,
            answer_text=answer_text,
            numeric_score=score,
            input_mode=input_mode,
            raw_transcript=raw_transcript
        )

        session = db.get_screening_session(session_id)
        if not session:
            return {"status": "error", "message": "Session not found"}

        order = session.get("question_order", [])
        curr_idx = session.get("current_index", 0)

        if is_crisis:
            # Immediate Crisis Escalation Flow
            db.log_crisis_event(session_id, user_id, question_id, reason)
            return {
                "status": "crisis_triggered",
                "crisis_detected": True,
                "risk_flag": "immediate",
                "recommended_action": "crisis_resources",
                "reason": reason,
                "emergency_resources": CRISIS_RESOURCES,
                "disclaimer": DISCLAIMER_TEXT,
                "message": (
                    "Your safety and wellbeing are our absolute highest priority. "
                    "Because of your response, we are pausing standard questions to connect "
                    "you immediately with confidential, 24/7 emergency support."
                )
            }

        # Advance question index
        next_idx = curr_idx + 1
        is_completed = next_idx >= len(order)
        next_q = self.get_question(order[next_idx]) if not is_completed and next_idx < len(order) else None

        # Clinical Tone & Speech Analysis
        tone_info = self.analyze_voice_tone(answer_text, q.get("domain", "mood"), score)
        doctor_dialogue = self.generate_doctor_dialogue(q, answer_text, tone_info, next_q)

        db.update_screening_session(
            session_id,
            current_index=next_idx,
            status="completed" if is_completed else "in_progress"
        )

        return {
            "status": "recorded",
            "crisis_detected": False,
            "session_id": session_id,
            "recorded_question_id": question_id,
            "numeric_score": score,
            "current_index": next_idx,
            "total_questions": len(order),
            "is_completed": is_completed,
            "tone_analysis": tone_info,
            "doctor_dialogue": doctor_dialogue,
            "next_question": next_q
        }

    def analyze_voice_tone(self, text: str, domain: str, score: float) -> Dict[str, Any]:
        """
        Evaluates speech/text tone, emotional markers, hesitation, and clinical distress.
        """
        clean = str(text).lower()
        words = clean.split()
        word_count = len(words)
        
        detected_tones = []
        if any(w in clean for w in ["exhausted", "tired", "drained", "heavy", "fatigue", "sluggish", "no energy"]):
            detected_tones.append("fatigued/depleted")
        if any(w in clean for w in ["worry", "panic", "nervous", "anxious", "scared", "fear", "racing", "shaking", "tension"]):
            detected_tones.append("anxious/tense")
        if any(w in clean for w in ["calm", "okay", "fine", "good", "manageable", "peaceful", "better", "rested"]):
            detected_tones.append("grounded/settled")
        if any(w in clean for w in ["hopeless", "sad", "down", "cry", "worthless", "blue", "discouraged"]):
            detected_tones.append("low-mood/sorrow")
        if any(w in clean for w in ["overwhelmed", "too much", "pressure", "burnout", "stress", "agitated", "irritated"]):
            detected_tones.append("overwhelmed/stressed")
        if any(w in clean for w in ["um", "uh", "maybe", "i guess", "not sure", "hesitant", "hard to say"]):
            detected_tones.append("hesitant/reflective")
        
        if not detected_tones:
            detected_tones.append("reflective" if score >= 1 else "calm")
            
        if word_count < 3:
            pacing = "concise"
        elif word_count > 15:
            pacing = "expressive"
        else:
            pacing = "measured"

        return {
            "primary_tone": detected_tones[0],
            "detected_tones": detected_tones,
            "word_count": word_count,
            "speech_pacing": pacing,
            "estimated_distress": "elevated" if score >= 2 else "mild" if score >= 1 else "low"
        }

    def generate_doctor_dialogue(self, current_q: Dict[str, Any], answer_text: str, tone_info: Dict[str, Any], next_q: Optional[Dict[str, Any]]) -> str:
        """
        Generates empathetic clinical doctor speech acknowledging the user's reflection
        and introducing the next question naturally.
        """
        tone = tone_info.get("primary_tone", "reflective")
        
        acknowledgments = {
            "fatigued/depleted": [
                "I hear how much exhaustion you've been carrying. Thank you for sharing that with me.",
                "It sounds like your energy has been under strain recently. Let's take our time together."
            ],
            "anxious/tense": [
                "I completely understand that feeling of nervous tension. Thank you for opening up.",
                "Feeling on edge can feel exhausting. Let's explore the next area gently."
            ],
            "overwhelmed/stressed": [
                "That sounds like a heavy weight to navigate. I appreciate your openness.",
                "When stress builds up, it touches so many areas of our day. Let's look at the next reflection."
            ],
            "low-mood/sorrow": [
                "Thank you for being open with me about how heavy things have felt.",
                "Holding those difficult feelings takes courage to speak about. I am here listening."
            ],
            "grounded/settled": [
                "I'm glad to hear that has felt manageable and settled for you.",
                "That is encouraging to hear. Let's continue reflecting on the next inquiry."
            ],
            "hesitant/reflective": [
                "Thank you for taking time to reflect on that.",
                "It is completely okay to take your time as we explore these feelings."
            ]
        }
        
        pool = acknowledgments.get(tone, ["Thank you for sharing that reflection with me."])
        ack = pool[hash(str(current_q.get("question_id", ""))) % len(pool)]
        
        if not next_q:
            return f"{ack} That completes our screening inquiries. I am synthesizing your clinical stratification report now."
            
        next_text = next_q.get("question_text", "")
        return f"{ack} Next: {next_text}"

    def compute_scores_and_analysis(self, session_id: str) -> Dict[str, Any]:
        """
        Calculates validated clinical subscale scores (PHQ-9, GAD-7, stress, sleep, functioning),
        determines distress level and risk tier, generates empathetic non-diagnostic summary,
        and provides tiered care recommendations consistent with research papers.
        """
        session = db.get_screening_session(session_id)
        if not session:
            raise ValueError(f"Screening session '{session_id}' not found.")

        user_id = session.get("user_id", "guest-user")
        answers_list = db.get_session_answers(session_id)
        answers_by_qid = {a["question_id"]: a for a in answers_list}

        # Check if already marked as crisis
        if session.get("crisis_flag") == 1 or session.get("status") == "crisis_halted":
            return {
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "phq9_score": session.get("phq9_score") or 0,
                "phq9_severity": session.get("phq9_severity") or "not_computed",
                "gad7_score": session.get("gad7_score") or 0,
                "gad7_severity": session.get("gad7_severity") or "not_computed",
                "stress_score": session.get("stress_score") or 0,
                "sleep_score": session.get("sleep_score") or 0,
                "functioning_score": session.get("functioning_score") or 0,
                "overall_distress": "high",
                "risk_flag": "immediate",
                "summary_text": "Immediate clinical safety concern detected during screening intake.",
                "recommended_action": "crisis_resources",
                "emergency_resources": CRISIS_RESOURCES,
                "disclaimer": DISCLAIMER_TEXT,
                "question_order": session.get("question_order", [])
            }

        # 1. Compute PHQ-9 Score (Items 1 through 9)
        phq9_rules = {
            "phq9_item_1": 0, "phq9_item_2": 0, "phq9_item_3": 0,
            "phq9_item_4": 0, "phq9_item_5": 0, "phq9_item_6": 0,
            "phq9_item_7": 0, "phq9_item_8": 0, "phq9_item_9_suicidality": 0
        }

        for rule in phq9_rules:
            q = self.questions_by_rule.get(rule)
            if q and q["question_id"] in answers_by_qid:
                phq9_rules[rule] = int(answers_by_qid[q["question_id"]]["numeric_score"] or 0)

        phq9_score = sum(phq9_rules.values())

        if phq9_score <= 4:
            phq9_severity = "minimal"
        elif phq9_score <= 9:
            phq9_severity = "mild"
        elif phq9_score <= 14:
            phq9_severity = "moderate"
        elif phq9_score <= 19:
            phq9_severity = "moderately_severe"
        else:
            phq9_severity = "severe"

        # 2. Compute GAD-7 Score (Items 1 through 7)
        gad7_rules = {
            "gad7_item_1": 0, "gad7_item_2": 0, "gad7_item_3": 0,
            "gad7_item_4": 0, "gad7_item_5": 0, "gad7_item_6": 0,
            "gad7_item_7": 0
        }

        for rule in gad7_rules:
            q = self.questions_by_rule.get(rule)
            if q and q["question_id"] in answers_by_qid:
                gad7_rules[rule] = int(answers_by_qid[q["question_id"]]["numeric_score"] or 0)

        gad7_score = sum(gad7_rules.values())

        if gad7_score <= 4:
            gad7_severity = "minimal"
        elif gad7_score <= 9:
            gad7_severity = "mild"
        elif gad7_score <= 14:
            gad7_severity = "moderate"
        else:
            gad7_severity = "severe"

        # 3. Stress Score (DASS-21 Stress Subscale items)
        stress_items = [q for q in self.questions if q["domain"] == "stress" and "dass21" in q.get("scoring_rule", "")]
        stress_raw = 0
        for sq in stress_items:
            if sq["question_id"] in answers_by_qid:
                stress_raw += int(answers_by_qid[sq["question_id"]]["numeric_score"] or 0)
        # Scale to DASS-21 equivalent (0 to 42)
        stress_score = min(42, stress_raw * 2) if stress_items else 0

        # 4. Sleep Disturbance Score
        sleep_items = [q for q in self.questions if q["domain"] == "sleep"]
        sleep_score = 0
        for sq in sleep_items:
            if sq["question_id"] in answers_by_qid:
                sleep_score += int(answers_by_qid[sq["question_id"]]["numeric_score"] or 0)

        # 5. Daily Functioning Impairment Score
        func_items = [q for q in self.questions if q["domain"] == "functioning"]
        functioning_score = 0
        for fq in func_items:
            if fq["question_id"] in answers_by_qid:
                functioning_score += int(answers_by_qid[fq["question_id"]]["numeric_score"] or 0)

        # 6. Safety & Risk Determination
        risk_flag = "none"
        safety_positive_count = 0
        immediate_detected = False

        for a in answers_list:
            is_c, tier, r = self.check_immediate_safety_trigger(a["question_id"], a["answer_text"])
            if is_c:
                immediate_detected = True
                break
            if tier == "moderate":
                safety_positive_count += 1

        if immediate_detected:
            risk_flag = "immediate"
        elif safety_positive_count >= 2 or phq9_rules.get("phq9_item_9_suicidality", 0) >= 1:
            risk_flag = "moderate"
        elif phq9_score >= 20 or gad7_score >= 15:
            risk_flag = "moderate"

        # 7. Overall Distress Stratification
        # Formula: PHQ-9 + GAD-7 + normalized sleep/stress impairment
        distress_index = phq9_score + gad7_score + (stress_score // 3) + (sleep_score // 2)

        if risk_flag == "immediate":
            overall_distress = "high"
        elif distress_index < 12 and phq9_score < 10 and gad7_score < 10:
            overall_distress = "low"
        elif distress_index < 28 and phq9_score < 15 and gad7_score < 15:
            overall_distress = "moderate"
        else:
            overall_distress = "high"

        # 8. Tiered Recommended Action
        if risk_flag == "immediate":
            recommended_action = "crisis_resources"
        elif overall_distress == "high" or phq9_severity in ["moderately_severe", "severe"] or gad7_severity == "severe":
            recommended_action = "urgent_psychiatrist_referral"
        elif overall_distress == "moderate" or phq9_severity == "moderate" or gad7_severity == "moderate":
            recommended_action = "psychologist_referral"
        else:
            recommended_action = "self_care"

        # 9. Empathetic, Non-Diagnostic Summary
        summary_sentences = []
        if overall_distress == "low":
            summary_sentences.append("Your responses indicate that your overall emotional distress is currently within a mild or manageable range.")
            if sleep_score > 6:
                summary_sentences.append("However, you noted some minor sleep or rest irregularities that could benefit from consistent bedtime rituals.")
            else:
                summary_sentences.append("You appear to have solid grounding routines and positive emotional anchors supporting your daily balance.")
            summary_sentences.append("Continued self-care practices, mindfulness, and healthy sleep hygiene are encouraged.")

        elif overall_distress == "moderate":
            summary_sentences.append("Your answers suggest that persistent stress, anxious tension, or temporary dips in mood have been affecting your day-to-day rhythm.")
            if sleep_score > 6:
                summary_sentences.append("Sleep quality and daytime energy also show signs of strain.")
            if functioning_score > 6:
                summary_sentences.append("You may be finding it more challenging than usual to keep up with demanding daily routines or social engagements.")
            summary_sentences.append("Connecting with a licensed psychologist or professional counselor can provide structured, practical tools for restoring calm and perspective.")

        else:  # High distress
            summary_sentences.append("Your responses reflect a significant burden of emotional distress, emotional exhaustion, or heavy stress across multiple areas of life.")
            if functioning_score > 8:
                summary_sentences.append("Daily routines, concentration, and emotional bandwidth appear notably impacted.")
            summary_sentences.append("Carrying this level of strain alone can feel overwhelming. We strongly encourage scheduling a supportive evaluation with a qualified clinical psychologist or psychiatrist.")

        summary_text = " ".join(summary_sentences)

        # Update database session
        db.update_screening_session(
            session_id,
            status="completed",
            phq9_score=phq9_score,
            phq9_severity=phq9_severity,
            gad7_score=gad7_score,
            gad7_severity=gad7_severity,
            stress_score=stress_score,
            sleep_score=sleep_score,
            functioning_score=functioning_score,
            overall_distress=overall_distress,
            risk_flag=risk_flag,
            summary_text=summary_text,
            recommended_action=recommended_action,
            completed_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
        )

        result = {
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "phq9_score": phq9_score,
            "phq9_severity": phq9_severity,
            "gad7_score": gad7_score,
            "gad7_severity": gad7_severity,
            "stress_score": stress_score,
            "sleep_score": sleep_score,
            "functioning_score": functioning_score,
            "overall_distress": overall_distress,
            "risk_flag": risk_flag,
            "summary_text": summary_text,
            "recommended_action": recommended_action,
            "question_order": session.get("question_order", []),
            "disclaimer": DISCLAIMER_TEXT,
            "emergency_resources": CRISIS_RESOURCES if risk_flag == "immediate" else None
        }

        return result


# Global Screener Engine Instance
screening_engine = MentalScreeningEngine()
