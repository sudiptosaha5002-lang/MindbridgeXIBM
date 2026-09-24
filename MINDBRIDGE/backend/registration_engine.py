"""
MindBridge Registration Mental-State Understanding Module
Orchestrates the 20-question registration interview lifecycle, safety checks, and non-diagnostic summary generation.
"""

import uuid
import json
import os
from typing import Dict, List, Any, Optional

from crisis_detector import crisis_detector
import google.generativeai as genai
from prompts import MINDBRIDGE_REGISTRATION_SYSTEM_PROMPT

REGISTRATION_QUESTIONS_FILE = os.path.join(os.path.dirname(__file__), "registration_questions.json")

class RegistrationEngine:
    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.questions = self._load_questions()

    def _load_questions(self) -> List[Dict[str, Any]]:
        if os.path.exists(REGISTRATION_QUESTIONS_FILE):
            with open(REGISTRATION_QUESTIONS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def start_session(self, user_id: str, language: str = "en") -> Dict[str, Any]:
        session_id = f"reg_sess_{uuid.uuid4().hex[:12]}"
        
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "language": language,
            "current_index": 0,
            "total_questions": len(self.questions),
            "status": "in_progress",
            "answers": []
        }
        
        self.active_sessions[session_id] = session_data
        
        first_q = self.questions[0] if self.questions else None
        
        return {
            "session_id": session_id,
            "language": language,
            "current_index": 0,
            "total_questions": len(self.questions),
            "question": first_q,
            "status": "in_progress"
        }

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.active_sessions.get(session_id)

    def get_current_question(self, session_id: str) -> Optional[Dict[str, Any]]:
        session = self.get_session(session_id)
        if not session or session["status"] != "in_progress":
            return None
        idx = session["current_index"]
        if idx < len(self.questions):
            return self.questions[idx]
        return None

    def submit_answer(self, session_id: str, answer_text: str, input_mode: str = "text", skipped: bool = False) -> Dict[str, Any]:
        session = self.get_session(session_id)
        if not session or session["status"] != "in_progress":
            return {"status": "error", "message": "Session invalid or already completed."}

        # Check for crisis before accepting answer
        if not skipped and answer_text:
            crisis_res = crisis_detector.check_crisis(answer_text)
            if crisis_res.get("risk_flag") in ["high", "immediate"]:
                session["status"] = "crisis_halted"
                return {
                    "status": "crisis_halted",
                    "crisis_data": crisis_res,
                    "message": "Immediate crisis detected. Stopping registration."
                }

        idx = session["current_index"]
        question = self.questions[idx]
        
        session["answers"].append({
            "question_id": question["id"],
            "domain": question["domain"],
            "question_text": question.get(session["language"], question["en"]),
            "answer_text": answer_text,
            "input_mode": input_mode,
            "skipped": skipped
        })

        session["current_index"] += 1
        
        if session["current_index"] >= len(self.questions):
            session["status"] = "completed"
            return {"status": "completed"}
            
        next_q = self.questions[session["current_index"]]
        return {
            "status": "in_progress",
            "next_question": next_q,
            "current_index": session["current_index"],
            "total_questions": session["total_questions"]
        }
        
    def analyze_session(self, session_id: str) -> Dict[str, Any]:
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found."}
            
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return {"error": "API Key not configured."}
            
        genai.configure(api_key=api_key)
        
        # Build transcript
        transcript = ""
        for a in session["answers"]:
            transcript += f"Q: {a['question_text']}\nA: {a['answer_text'] if not a['skipped'] else '(Skipped)'}\n\n"
            
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=MINDBRIDGE_REGISTRATION_SYSTEM_PROMPT
        )
        
        try:
            response = model.generate_content(
                f"Analyze the following user registration interview and provide the JSON summary:\n\n{transcript}",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)
        except Exception as e:
            return {"error": str(e)}

registration_engine = RegistrationEngine()
