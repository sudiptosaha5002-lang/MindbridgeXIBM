"""
MindBridge Emotion Interview Engine.
====================================
Orchestrates the 10-question gentle emotion interview lifecycle:
- Manages active interview sessions and state machine.
- Provides question sequencing in English, Bengali, and Hindi.
- Validates and stores verified user answers (voice / text).
- Coordinates with EmotionAnalyzer to synthesize the final Emotional State Profile.
"""

import uuid
from typing import Dict, List, Any, Optional
from emotion_questions import emotion_questions_repo
from emotion_detector import emotion_detector
from emotion_analyzer import emotion_analyzer
import database as db

class EmotionInterviewEngine:
    def __init__(self):
        self.repo = emotion_questions_repo
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

    def start_session(
        self,
        user_id: str,
        conversation_id: Optional[str] = None,
        language: str = "en",
        trigger_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Starts a new Emotion Interview session.
        """
        session_id = f"emo_sess_{uuid.uuid4().hex[:12]}"
        questions = self.repo.get_all_questions(language=language)
        total_questions = len(questions)

        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "conversation_id": conversation_id,
            "language": language,
            "trigger_reason": trigger_reason or "user_emotional_expression",
            "current_index": 0,
            "total_questions": total_questions,
            "status": "in_progress",
            "answers": []
        }

        self.active_sessions[session_id] = session_data

        # Persist in DB
        db.create_emotion_session(
            session_id=session_id,
            user_id=user_id,
            conversation_id=conversation_id,
            language=language,
            trigger_reason=trigger_reason,
            total_questions=total_questions
        )

        first_q = questions[0] if questions else None

        return {
            "session_id": session_id,
            "language": language,
            "current_index": 0,
            "total_questions": total_questions,
            "question": first_q,
            "status": "in_progress"
        }

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves active session state in memory or loads from database.
        """
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]

        db_sess = db.get_emotion_session(session_id)
        if not db_sess:
            return None

        db_answers = db.get_emotion_answers(session_id)
        sess = {
            "session_id": db_sess["id"],
            "user_id": db_sess["user_id"],
            "conversation_id": db_sess["conversation_id"],
            "language": db_sess["language"],
            "trigger_reason": db_sess["trigger_reason"],
            "current_index": db_sess["current_index"],
            "total_questions": db_sess["total_questions"],
            "status": db_sess["status"],
            "answers": db_answers
        }
        self.active_sessions[session_id] = sess
        return sess

    def get_question_at_index(self, session_id: str, index: int) -> Optional[Dict[str, Any]]:
        session = self.get_session(session_id)
        if not session:
            return None
        lang = session.get("language", "en")
        questions = self.repo.get_all_questions(language=lang)
        if 0 <= index < len(questions):
            return questions[index]
        return None

    def process_answer(
        self,
        session_id: str,
        answer_text: str,
        input_mode: str = "voice",
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submits and records confirmed answer for current question.
        Advances state machine to the next question or finalizes interview.
        """
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found", "is_complete": False}

        lang = session.get("language", "en")
        curr_idx = session.get("current_index", 0)
        questions = self.repo.get_all_questions(language=lang)

        if curr_idx >= len(questions):
            # Already completed
            analysis = self.finalize_session(session_id)
            return {
                "session_id": session_id,
                "is_complete": True,
                "current_index": curr_idx,
                "total_questions": len(questions),
                "analysis": analysis
            }

        curr_q = questions[curr_idx]
        uid = user_id or session.get("user_id", "guest-user")

        # Run real-time emotion detection on this specific answer
        det = emotion_detector.detect_emotion(answer_text, language=lang)

        answer_record = {
            "question_id": curr_q["id"],
            "theme": curr_q["theme"],
            "question_text": curr_q["question_text"],
            "answer_text": answer_text,
            "input_mode": input_mode,
            "detected_emotions": [e["label"] for e in det.get("detected_emotions", [])],
            "intensity": det.get("intensity", "moderate"),
            "sensitivity_flags": det.get("sensitivity_flags", ["none"])
        }

        session.setdefault("answers", []).append(answer_record)

        # Persist answer to SQLite
        db.record_emotion_answer(
            session_id=session_id,
            user_id=uid,
            question_id=curr_q["id"],
            theme=curr_q["theme"],
            question_text=curr_q["question_text"],
            answer_text=answer_text,
            input_mode=input_mode,
            detected_emotions=[e["label"] for e in det.get("detected_emotions", [])],
            intensity=det.get("intensity", "moderate"),
            sensitivity_flags=det.get("sensitivity_flags", ["none"])
        )

        next_idx = curr_idx + 1
        session["current_index"] = next_idx
        is_complete = next_idx >= len(questions)

        db.update_emotion_session(session_id, current_index=next_idx)

        analysis = None
        next_q = None

        if is_complete:
            session["status"] = "completed"
            analysis = self.finalize_session(session_id)
        else:
            next_q = questions[next_idx]

        return {
            "session_id": session_id,
            "is_complete": is_complete,
            "current_index": next_idx,
            "total_questions": len(questions),
            "next_question": next_q,
            "analysis": analysis
        }

    def finalize_session(self, session_id: str) -> Dict[str, Any]:
        """
        Runs comprehensive analysis on all submitted answers and persists report.
        """
        session = self.get_session(session_id)
        if not session:
            return {}

        answers = session.get("answers", [])
        if not answers:
            answers = db.get_emotion_answers(session_id)

        lang = session.get("language", "en")
        analysis = emotion_analyzer.analyze_interview_answers(answers, language=lang)

        db.update_emotion_session(
            session_id,
            status="completed",
            dominant_emotions=analysis.get("dominant_emotions", []),
            overall_intensity=analysis.get("overall_intensity", "low"),
            coping_style=analysis.get("coping_style", "mixed"),
            themes_identified=analysis.get("themes", []),
            narrative_summary=analysis.get("emotional_state_summary", ""),
            completed_at="CURRENT_TIMESTAMP"
        )

        return analysis

# Global singleton
emotion_interview_engine = EmotionInterviewEngine()
