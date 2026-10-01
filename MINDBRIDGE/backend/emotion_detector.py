"""
MindBridge Emotion Detection & Classification Engine.
=====================================================
Analyzes user inputs (text or transcribed audio) and recent conversational context
to classify emotional states, measure intensity, detect clinical sensitivity flags,
and determine whether an Emotion Interview should be triggered.

Categories:
- sadness, anxiety, anger, fear, guilt, shame, loneliness, hopelessness,
  joy, relief, calm, numbness, overwhelm, other

Intensity:
- low, moderate, high

Sensitivity Flags:
- self_harm_thoughts, suicidal_feelings, trauma_reference, intense_emotional_pain, none
"""

import os
import json
import re
from typing import Dict, List, Optional, Any, Tuple

# ---------------------------------------------------------------------------
# 1. LOAD LEXICONS FROM JSON
# ---------------------------------------------------------------------------

LEXICON_FILE = os.path.join(os.path.dirname(__file__), "emotion_lexicons.json")

def load_lexicons():
    try:
        with open(LEXICON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Flatten multilingual lexicons into single lists per category
            flat_emotions = {}
            for cat, langs in data.get("emotions", {}).items():
                flat_emotions[cat] = []
                for lang, words in langs.items():
                    flat_emotions[cat].extend(words)
                    
            flat_safety = {}
            for cat, langs in data.get("safety_phrases", {}).items():
                flat_safety[cat] = []
                for lang, words in langs.items():
                    # Keep as regex patterns
                    flat_safety[cat].extend(words)

            high_intensity = []
            for words in data.get("intensity_modifiers", {}).get("high", {}).values():
                high_intensity.extend(words)
            low_intensity = []
            for words in data.get("intensity_modifiers", {}).get("low", {}).values():
                low_intensity.extend(words)
                
            return flat_emotions, flat_safety, high_intensity, low_intensity
    except Exception as e:
        print(f"[Warning] Could not load emotion_lexicons.json: {e}")
        return {}, {}, [], []

EMOTION_LEXICONS, SENSITIVITY_PATTERNS_RAW, HIGH_INTENSITY_MODIFIERS_RAW, LOW_INTENSITY_MODIFIERS_RAW = load_lexicons()

# Convert safety raw lists to regex strings (word boundaries)
SENSITIVITY_PATTERNS = {}
for cat, phrases in SENSITIVITY_PATTERNS_RAW.items():
    # Only latin words get \b. Indic words don't.
    patterns = []
    for p in phrases:
        if any(ord(c) > 127 for c in p):
            patterns.append(re.escape(p))
        else:
            patterns.append(r"\b" + re.escape(p) + r"\b")
    SENSITIVITY_PATTERNS[cat] = patterns

HIGH_INTENSITY_MODIFIERS = [
    r"\b(" + "|".join([re.escape(w) for w in HIGH_INTENSITY_MODIFIERS_RAW if not any(ord(c) > 127 for c in w)]) + r")\b",
    r"(" + "|".join([re.escape(w) for w in HIGH_INTENSITY_MODIFIERS_RAW if any(ord(c) > 127 for c in w)]) + r")"
]

LOW_INTENSITY_MODIFIERS = [
    r"\b(" + "|".join([re.escape(w) for w in LOW_INTENSITY_MODIFIERS_RAW if not any(ord(c) > 127 for c in w)]) + r")\b",
    r"(" + "|".join([re.escape(w) for w in LOW_INTENSITY_MODIFIERS_RAW if any(ord(c) > 127 for c in w)]) + r")"
]

class EmotionDetector:
    """
    Multilingual emotion and sensitivity detector for MindBridge.
    """

    def __init__(self):
        self.lexicons = EMOTION_LEXICONS
        self.sensitivity_patterns = SENSITIVITY_PATTERNS

    def detect_emotion(
        self,
        text: str,
        context_messages: Optional[List[Dict[str, Any]]] = None,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Main classifier:
        Analyzes user input text and conversation history.
        
        Returns:
        {
          "is_emotional": bool,
          "emotion_categories": List[str],
          "primary_emotion": str,
          "intensity": "low" | "moderate" | "high",
          "sensitivity_flags": List[str],
          "trigger_interview": bool,
          "confidence": float,
          "matched_signals": Dict[str, Any]
        }
        """
        clean_text = (text or "").strip()
        if not clean_text:
            return {
                "is_emotional": False,
                "emotion_categories": [],
                "primary_emotion": "neutral",
                "intensity": "low",
                "sensitivity_flags": ["none"],
                "trigger_interview": False,
                "confidence": 0.0,
                "matched_signals": {}
            }

        lower_text = clean_text.lower()
        detected_categories: Dict[str, int] = {}
        matched_keywords: Dict[str, List[str]] = {}

        # 1. Lexical and phrase matching on current text
        for category, keywords in self.lexicons.items():
            for kw in keywords:
                # Word boundary check for latin, substring for Indic
                is_indic = any(ord(c) > 127 for c in kw)
                matched = False
                if is_indic:
                    if kw.lower() in lower_text:
                        matched = True
                else:
                    pattern = r"(?:\b|_)" + re.escape(kw.lower()) + r"(?:\b|_)"
                    if re.search(pattern, lower_text):
                        matched = True

                if matched:
                    detected_categories[category] = detected_categories.get(category, 0) + 1
                    matched_keywords.setdefault(category, []).append(kw)

        # 2. Contextual multi-turn reinforcement (last 3-5 messages)
        context_boosts: Dict[str, int] = {}
        if context_messages and isinstance(context_messages, list):
            recent_user_turns = [
                m.get("content", "") for m in context_messages[-5:]
                if m.get("sender") == "user" or m.get("role") == "user"
            ]
            for turn in recent_user_turns:
                turn_lower = turn.lower()
                for category, keywords in self.lexicons.items():
                    for kw in keywords:
                        is_indic = any(ord(c) > 127 for c in kw)
                        if is_indic and kw.lower() in turn_lower:
                            context_boosts[category] = context_boosts.get(category, 0) + 1
                        elif not is_indic and re.search(r"\b" + re.escape(kw.lower()) + r"\b", turn_lower):
                            context_boosts[category] = context_boosts.get(category, 0) + 1

        # Merge context score (weighted 0.5)
        combined_scores: Dict[str, float] = {}
        for cat, cnt in detected_categories.items():
            combined_scores[cat] = float(cnt) + context_boosts.get(cat, 0) * 0.5

        for cat, cnt in context_boosts.items():
            if cat not in combined_scores:
                combined_scores[cat] = cnt * 0.5

        # 3. Detect Clinical Sensitivity Flags
        detected_sensitivity: List[str] = []
        for flag_name, patterns in self.sensitivity_patterns.items():
            for pat in patterns:
                if re.search(pat, lower_text, re.IGNORECASE):
                    if flag_name not in detected_sensitivity:
                        detected_sensitivity.append(flag_name)

        if not detected_sensitivity:
            detected_sensitivity = ["none"]

        # 4. Intensity Evaluation
        has_high_modifier = any(re.search(pat, lower_text, re.IGNORECASE) for pat in HIGH_INTENSITY_MODIFIERS)
        has_low_modifier = any(re.search(pat, lower_text, re.IGNORECASE) for pat in LOW_INTENSITY_MODIFIERS)
        
        # Punctuation/Exclamation markers
        exclamation_count = clean_text.count("!") + clean_text.count("...")
        
        has_sensitive_flag = any(f != "none" for f in detected_sensitivity)
        total_emotion_hits = sum(detected_categories.values())

        intensity = "low"
        if has_sensitive_flag or has_high_modifier or total_emotion_hits >= 3 or exclamation_count >= 2:
            intensity = "high"
        elif total_emotion_hits >= 1 or has_low_modifier or len(combined_scores) > 0:
            intensity = "moderate" if not has_low_modifier else "low"

        # 5. Determine Primary Emotion & Overall State
        sorted_emotions = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        emotion_categories = [cat for cat, score in sorted_emotions if score >= 0.5]

        # Check for specific phrase patterns that imply emotion even without exact word hits
        implied_pain = re.search(r"\b(i\s*can'?t\s*do\s*this|feel\s*like\s*giving\s*up|so\s*hard\s*right\s*now|everything\s*is\s*falling\s*apart)\b", lower_text)
        if implied_pain:
            if "overwhelm" not in emotion_categories:
                emotion_categories.append("overwhelm")
            if "hopelessness" not in emotion_categories:
                emotion_categories.append("hopelessness")
            if intensity == "low":
                intensity = "moderate"

        is_emotional = (len(emotion_categories) > 0) or has_sensitive_flag
        primary_emotion = emotion_categories[0] if emotion_categories else ("intense_pain" if has_sensitive_flag else "neutral")

        # 6. Trigger Decision
        # Moderate/High intensity emotion OR sensitive flags trigger the Emotion Interview
        trigger_interview = False
        if is_emotional:
            if has_sensitive_flag:
                trigger_interview = True
            elif intensity in ["moderate", "high"]:
                # High/moderate distress emotions trigger the interview
                distress_categories = {"sadness", "anxiety", "anger", "fear", "guilt", "shame", "loneliness", "hopelessness", "numbness", "overwhelm"}
                if any(c in distress_categories for c in emotion_categories):
                    trigger_interview = True

        # Confidence calculation
        confidence = 0.5
        if is_emotional:
            confidence = min(0.98, 0.65 + (total_emotion_hits * 0.1) + (0.15 if has_sensitive_flag else 0.0))
        else:
            confidence = 0.90

        # Check code-mixing (e.g. mix of latin and indic characters)
        has_latin = any(c.isascii() and c.isalpha() for c in clean_text)
        has_indic = any(ord(c) > 127 for c in clean_text)
        is_code_mixed = has_latin and has_indic

        # Format detected emotions with scores
        detected_emotions = []
        for cat, score in sorted_emotions:
            if score >= 0.5:
                # Normalize score to 0-1 range for the output
                norm_score = round(min(0.99, 0.5 + (score * 0.1)), 2)
                detected_emotions.append({"label": cat, "score": norm_score})

        # Determine risk flag
        risk_flag = "none"
        if "suicidal_feelings" in detected_sensitivity or "self_harm_thoughts" in detected_sensitivity:
            risk_flag = "immediate"
        elif "intense_emotional_pain" in detected_sensitivity:
            risk_flag = "high"
        elif "trauma_reference" in detected_sensitivity:
            risk_flag = "moderate"

        # Map some themes based on emotions
        themes = []
        if "anxiety" in emotion_categories or "overwhelm" in emotion_categories:
            themes.append("stress")
        if "loneliness" in emotion_categories or "sadness" in emotion_categories:
            themes.append("isolation")
        if "emotional_exhaustion" in emotion_categories or "overwhelm" in emotion_categories:
            themes.append("fatigue")

        return {
            "is_emotional": bool(is_emotional),
            "language": language,
            "is_code_mixed": is_code_mixed,
            "detected_emotions": detected_emotions,
            "dominant_emotion": primary_emotion,
            "intensity": intensity,
            "themes": themes,
            "sensitivity_flags": detected_sensitivity if detected_sensitivity != ["none"] else [],
            "risk_flag": risk_flag,
            "needs_emotion_interview": bool(trigger_interview),
            "confidence": round(confidence, 2)
        }

# Global singleton
emotion_detector = EmotionDetector()
