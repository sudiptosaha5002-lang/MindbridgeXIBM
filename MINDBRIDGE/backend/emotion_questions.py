"""
MindBridge Emotion Interview Questions Repository.
Provides access to the 10 refined, gentle emotion-focused questions
with native tri-lingual support (English, Bengali, Hindi), supportive guidance,
and contextual response chips.
"""

import os
import json
from typing import Dict, List, Optional, Any

QUESTIONS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "emotion_questions.json")

class EmotionQuestionsRepository:
    def __init__(self, questions_path: str = QUESTIONS_FILE):
        self.questions_path = questions_path
        self.questions: List[Dict[str, Any]] = []
        self.questions_by_id: Dict[int, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.questions_path):
            with open(self.questions_path, "r", encoding="utf-8") as f:
                self.questions = json.load(f)
                for q in self.questions:
                    self.questions_by_id[q["id"]] = q
        else:
            self.questions = []
            self.questions_by_id = {}

    def get_all_questions(self, language: str = "en") -> List[Dict[str, Any]]:
        """
        Returns all 10 emotion questions formatted for the requested language (en, bn, hi).
        """
        lang = "bn" if language.startswith("bn") else "hi" if language.startswith("hi") else "en"
        results = []
        for q in self.questions:
            results.append({
                "id": q["id"],
                "theme": q["theme"],
                "question_text": q["question_text"].get(lang, q["question_text"].get("en", "")),
                "gentle_support": q["gentle_support"].get(lang, q["gentle_support"].get("en", "")),
                "suggested_chips": q["suggested_chips"].get(lang, q["suggested_chips"].get("en", [])),
                "language": lang
            })
        return results

    def get_question_by_id(self, question_id: int, language: str = "en") -> Optional[Dict[str, Any]]:
        q = self.questions_by_id.get(question_id)
        if not q:
            return None
        lang = "bn" if language.startswith("bn") else "hi" if language.startswith("hi") else "en"
        return {
            "id": q["id"],
            "theme": q["theme"],
            "question_text": q["question_text"].get(lang, q["question_text"].get("en", "")),
            "gentle_support": q["gentle_support"].get(lang, q["gentle_support"].get("en", "")),
            "suggested_chips": q["suggested_chips"].get(lang, q["suggested_chips"].get("en", [])),
            "language": lang
        }

# Global singleton
emotion_questions_repo = EmotionQuestionsRepository()
