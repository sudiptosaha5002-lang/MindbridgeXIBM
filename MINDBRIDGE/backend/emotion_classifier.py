import os
import json
import logging
from typing import Dict, Any, List, Optional
from crisis_detector import crisis_detector
from prompts import SYSTEM_PROMPT

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

logger = logging.getLogger(__name__)

class EmotionClassifier:
    """
    LLM-powered emotion and category classifier using Google Gemini.
    """
    
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.model = None
        
        if HAS_GENAI and self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=SYSTEM_PROMPT,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.2 # low temperature for classification stability
                )
            )
        else:
            logger.warning("GEMINI_API_KEY not found or google-generativeai not installed. Falling back to basic mock classifier.")

    def classify_input(self, text: str, context: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        clean_text = (text or "").strip()

        # 1. Fallback / Unclear checks (Before LLM to save tokens/time)
        if len(clean_text) < 2 or clean_text == "...":
            return self._build_fallback_response("Input too short or empty.")
            
        # 2. Pre-classification Crisis Check (Mandated by safety rules)
        # Even though LLM can detect it, we run our deterministic rule engine first for absolute safety.
        crisis_eval = crisis_detector.check_crisis(clean_text)
        if crisis_eval.get("risk_flag") in ["high", "immediate", "emergency"]:
            return {
                "language": "en",
                "is_code_mixed": False,
                "input_category": "emergency_safety_input",
                "is_emotional": True,
                "detected_emotions": ["fear", "distress"],
                "emotion_intensity": "high",
                "time_scope": "current",
                "themes": ["safety"],
                "coping_style": None,
                "risk_flag": crisis_eval.get("risk_flag"),
                "classification_confidence": 0.99,
                "expected_chatbot_response": "I hear you, and your safety is important. Please contact emergency services right now.",
                "next_action": "activate_crisis_flow",
                "stop_normal_screening": True
            }

        # 3. LLM Classification
        if self.model:
            try:
                response = self.model.generate_content(clean_text)
                result_json = json.loads(response.text)
                
                # Double check LLM crisis flag just in case rule-based missed it
                if result_json.get("risk_flag") in ["high", "immediate"]:
                    result_json["next_action"] = "activate_crisis_flow"
                    result_json["stop_normal_screening"] = True
                    
                # Double check confidence threshold for fallback trigger
                conf = result_json.get("classification_confidence", 1.0)
                if conf < 0.65 or result_json.get("input_category") == "unclear_or_unknown_input":
                    result_json["next_action"] = "open_fallback_emotion_window"
                    
                return result_json
            except Exception as e:
                logger.error(f"LLM Classification failed: {e}")
                return self._build_fallback_response(str(e))
        else:
            # Basic Regex Fallback if API is missing
            return self._mock_regex_classify(clean_text)

    def _build_fallback_response(self, reason: str) -> Dict[str, Any]:
        return {
            "language": "en",
            "is_code_mixed": False,
            "input_category": "unclear_or_unknown_input",
            "is_emotional": False,
            "detected_emotions": ["uncertain"],
            "emotion_intensity": "unknown",
            "time_scope": "unknown",
            "themes": [],
            "coping_style": None,
            "risk_flag": "none",
            "classification_confidence": 0.40,
            "expected_chatbot_response": "That is completely okay. Sometimes it can be hard to put feelings into words. Would you like to answer a few simple questions that may help you reflect on how you have been feeling?",
            "next_action": "open_fallback_emotion_window",
            "stop_normal_screening": False
        }
        
    def _mock_regex_classify(self, text: str) -> Dict[str, Any]:
        # Minimal mock fallback for testing without API key
        if "sad" in text.lower():
            cat = "sadness_grief_input"
            act = "offer_emotion_interview"
            conf = 0.85
        elif "anxious" in text.lower():
            cat = "anxiety_stress_input"
            act = "offer_emotion_interview"
            conf = 0.85
        else:
            cat = "neutral_input"
            act = "continue_normal_flow"
            conf = 0.80
            
        return {
            "language": "en",
            "is_code_mixed": False,
            "input_category": cat,
            "is_emotional": True,
            "detected_emotions": ["unknown"],
            "emotion_intensity": "moderate",
            "time_scope": "current",
            "themes": [],
            "coping_style": None,
            "risk_flag": "none",
            "classification_confidence": conf,
            "expected_chatbot_response": "Auto-generated mock response.",
            "next_action": act,
            "stop_normal_screening": False
        }

# Singleton instance
emotion_classifier = EmotionClassifier()
