"""
MindBridge Emotional-State Analysis & Synthesis Engine.
======================================================
Analyzes completed or in-progress Emotion Interview responses, extracts
dominant emotional dimensions, themes, coping mechanisms, and generates
an empathetic, non-diagnostic summary integrated into the overall mental-state report.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from emotion_detector import emotion_detector, EMOTION_LEXICONS

# ---------------------------------------------------------------------------
# 1. THEMATIC KEYWORD DICTIONARY
# ---------------------------------------------------------------------------

THEME_LEXICONS: Dict[str, Dict[str, Any]] = {
    "past_trauma": {
        "label": "Past Emotional Echoes & Trauma",
        "keywords": ["past", "memory", "loss", "childhood", "hurt", "abuse", "loss still hurts", "old memory", "অতীত", "পুরনো স্মৃতি", "কষ্টদায়ক স্মৃতি", "পুরানি ইয়াদ", "पुराना दर्द"]
    },
    "relationship_stress": {
        "label": "Relational Friction & Interpersonal Attachment",
        "keywords": ["partner", "relationship", "friend", "family", "parents", "conflict", "breakup", "lonely", "cheated", "সম্পর্ক", "পরিবার", "মা-বাবা", "ব্রেকআপ", "रिश्ता", "परिवार", "दोस्त"]
    },
    "work_study_pressure": {
        "label": "Workplace & Academic Burnout",
        "keywords": ["work", "job", "career", "study", "exam", "deadlines", "office", "target", "money", "চাকরি", "পড়াশোনা", "পরীক্ষা", "অফিস", "काम", "नौकरी", "पढ़ाई", "परीक्षा"]
    },
    "self_worth_issues": {
        "label": "Self-Worth & Inner Criticism",
        "keywords": ["worthless", "failure", "not good enough", "blame myself", "inferior", "embarrassed", "লজ্জা", "অযোগ্য", "ব্যর্থতা", "खुद को दोष", "नाकाबिल", "कमजोरी"]
    },
    "emotional_suppression": {
        "label": "Emotional Guardedness & Suppression",
        "keywords": ["bottle it up", "keep inside", "hide", "suppress", "hold back", "fear of judgment", "don't want to burden", "চেপে রাখা", "লুকিয়ে রাখা", "প্রকাশ করি না", "दबा लेता हूँ", "छिपाना", "व्यक्त नहीं करता"]
    },
    "existential_uncertainty": {
        "label": "Future Uncertainty & Existential Strain",
        "keywords": ["future", "uncertainty", "what will happen", "directionless", "purpose", "lost", "ভবিষ্যত", "অনিশ্চয়তা", "কোন পথ নেই", "भविष्य", "अनिश्चितता", "दिशाहीन"]
    }
}

# ---------------------------------------------------------------------------
# 2. COPING STYLE CLASSIFIER
# ---------------------------------------------------------------------------

HEALTHY_COPING_SIGNALS = [
    "talk to someone", "exercise", "walk", "writing", "journaling", "crying", "music",
    "nature", "deep breaths", "reach out", "therapy", "rest", "boundaries", "sleep",
    "কথা বলা", "ডায়েরি লেখা", "হাঁটা", "গান শোনা", "কেঁদে মন হালকা", "বিশ্রাম",
    "बात करना", "टहलना", "डायरी लिखना", "संगीत", "रोकर हल्का होना", "आराम"
]

AVOIDANT_COPING_SIGNALS = [
    "withdraw", "isolate", "bottle it up", "hide", "suppress", "ignore it",
    "distract myself endlessly", "sleep all day", "stay quiet", "avoid people",
    "নিজেকে গুটিয়ে নিই", "একাকী থাকা", "ভেতরে চেপে রাখি", "এড়িয়ে চলি",
    "अलग-थलग हो जाना", "अंदर ही दबाना", "बात टालना", "किसी से न मिलना"
]

class EmotionAnalyzer:
    """
    Aggregates multi-question interview responses and generates comprehensive
    emotional synthesis reports.
    """

    def __init__(self):
        self.theme_lexicons = THEME_LEXICONS
        self.healthy_coping = HEALTHY_COPING_SIGNALS
        self.avoidant_coping = AVOIDANT_COPING_SIGNALS

    def analyze_interview_answers(
        self,
        answers: List[Dict[str, Any]],
        language: str = "en",
        user_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Processes a list of question answers:
        [
          {
            "question_id": 1,
            "theme": "present_state",
            "question_text": "...",
            "answer_text": "I feel really anxious and exhausted",
            "input_mode": "voice" | "text"
          }, ...
        ]
        """
        if not answers:
            return {
                "dominant_emotions": ["reflective"],
                "intensity": "low",
                "themes": [],
                "coping_style": "balanced",
                "emotional_state_summary": "No emotion interview answers provided.",
                "metrics": {"emotional_clarity": 50, "vulnerability_index": 50, "resilience_score": 50}
            }

        all_text = " ".join([a.get("answer_text", "") for a in answers if a.get("answer_text")]).strip()
        all_text_lower = all_text.lower()

        # 1. Aggregate emotion occurrences across all answers
        emotion_frequency: Dict[str, int] = {}
        for ans in answers:
            ans_text = ans.get("answer_text", "")
            if not ans_text:
                continue
            det = emotion_detector.detect_emotion(ans_text, language=language)
            for e in det.get("detected_emotions", []):
                cat = e["label"]
                emotion_frequency[cat] = emotion_frequency.get(cat, 0) + 1

        # Sort dominant emotions by frequency
        sorted_emotions = sorted(emotion_frequency.items(), key=lambda x: x[1], reverse=True)
        dominant_emotions = [cat for cat, cnt in sorted_emotions if cnt >= 1]
        if not dominant_emotions:
            dominant_emotions = ["calm", "reflective"]

        # 2. Overall Intensity Computation
        high_intensity_count = 0
        moderate_intensity_count = 0
        for ans in answers:
            ans_text = ans.get("answer_text", "")
            if not ans_text:
                continue
            det = emotion_detector.detect_emotion(ans_text, language=language)
            if det.get("intensity") == "high":
                high_intensity_count += 1
            elif det.get("intensity") == "moderate":
                moderate_intensity_count += 1

        if high_intensity_count >= 2 or (high_intensity_count >= 1 and moderate_intensity_count >= 3):
            overall_intensity = "high"
        elif (moderate_intensity_count + high_intensity_count) >= 2:
            overall_intensity = "moderate"
        else:
            overall_intensity = "low"

        # 3. Identify Thematic Domains
        detected_themes: List[Dict[str, Any]] = []
        for theme_key, theme_info in self.theme_lexicons.items():
            matched_kw = []
            for kw in theme_info["keywords"]:
                is_indic = any(ord(c) > 127 for c in kw)
                if is_indic and kw.lower() in all_text_lower:
                    matched_kw.append(kw)
                elif not is_indic and re.search(r"\b" + re.escape(kw.lower()) + r"\b", all_text_lower):
                    matched_kw.append(kw)

            if matched_kw:
                detected_themes.append({
                    "id": theme_key,
                    "label": theme_info["label"],
                    "hits": len(matched_kw),
                    "evidence": matched_kw[:3]
                })

        # 4. Coping Style Analysis
        healthy_score = sum(1 for sig in self.healthy_coping if (sig in all_text_lower if any(ord(c) > 127 for c in sig) else re.search(r"\b" + re.escape(sig) + r"\b", all_text_lower)))
        avoidant_score = sum(1 for sig in self.avoidant_coping if (sig in all_text_lower if any(ord(c) > 127 for c in sig) else re.search(r"\b" + re.escape(sig) + r"\b", all_text_lower)))

        if healthy_score > avoidant_score and healthy_score >= 1:
            coping_style = "healthy_coping"
            coping_label = "Active & Healthy Coping"
            coping_desc = "You actively utilize supportive strategies such as expressing thoughts, physical movement, and seeking calm."
        elif avoidant_score > healthy_score and avoidant_score >= 1:
            coping_style = "avoidant_coping"
            coping_label = "Avoidant / Emotional Suppression"
            coping_desc = "You often tend to hold feelings inside or isolate when overwhelmed, which may feel protective but can build inner tension."
        elif avoidant_score >= 1 and healthy_score >= 1:
            coping_style = "mixed_coping"
            coping_label = "Mixed Coping Pattern"
            coping_desc = "You balance some proactive coping with occasional withdrawal or emotional suppression."
        else:
            coping_style = "mixed_coping"
            coping_label = "Adaptive Exploration"
            coping_desc = "You are currently exploring various emotional management styles as needs arise."

        # 5. Core Emotional Metrics (0 - 100)
        total_answers = len([a for a in answers if a.get("answer_text")])
        openness_score = min(95, max(30, int(total_answers * 9 + healthy_score * 5)))
        resilience_score = min(95, max(35, int(50 + healthy_score * 8 - avoidant_score * 4)))
        emotional_load_score = min(95, max(20, int(30 + (high_intensity_count * 18) + (moderate_intensity_count * 8))))

        # 6. Generate Empathetic Non-Diagnostic Summary
        summary = self._generate_narrative_summary(
            dominant_emotions=dominant_emotions,
            overall_intensity=overall_intensity,
            detected_themes=detected_themes,
            coping_style=coping_style,
            coping_desc=coping_desc,
            language=language
        )

        return {
            "dominant_emotions": dominant_emotions,
            "overall_intensity": overall_intensity,
            "themes": detected_themes,
            "coping_style": coping_style,
            "coping_label": coping_label,
            "coping_description": coping_desc,
            "metrics": {
                "emotional_openness": openness_score,
                "resilience_score": resilience_score,
                "emotional_load": emotional_load_score
            },
            "emotional_state_summary": summary,
            "clinical_governance": {
                "is_diagnostic": False,
                "disclaimer": "This emotion interview is a supportive reflective tool and does not constitute a clinical psychiatric diagnosis."
            }
        }

    def _generate_narrative_summary(
        self,
        dominant_emotions: List[str],
        overall_intensity: str,
        detected_themes: List[Dict[str, Any]],
        coping_style: str,
        coping_desc: str,
        language: str = "en"
    ) -> str:
        lang = "bn" if language.startswith("bn") else "hi" if language.startswith("hi") else "en"
        emotions_str = ", ".join(dominant_emotions[:3]) if dominant_emotions else "reflective"

        theme_labels = [t["label"] for t in detected_themes[:2]]
        themes_str = f" relating to {', '.join(theme_labels)}" if theme_labels else ""

        if lang == "bn":
            bn_emotions = {
                "sadness": "বিষণ্ণতা", "anxiety": "উদ্বেগ", "anger": "রাগ", "fear": "ভয়",
                "guilt": "অপরাধবোধ", "shame": "লজ্জা", "loneliness": "একাকীত্ব",
                "hopelessness": "হতাশা", "overwhelm": "ভারাক্রান্ত অনুভূতি", "numbness": "অসাড়তা",
                "joy": "আনন্দ", "relief": "স্বস্তি", "calm": "প্রশান্তি"
            }
            bn_emo_list = [bn_emotions.get(e, e) for e in dominant_emotions[:3]]
            emo_bn_str = " এবং ".join(bn_emo_list) if bn_emo_list else "সংবেদনশীল অনুভূতি"

            return (
                f"আপনার উত্তরগুলোর ভিত্তিতে বোঝা যায়, আপনি বর্তমানে মূলত {emo_bn_str}-এর মধ্য দিয়ে যাচ্ছেন, "
                f"যার তীব্রতা {overall_intensity == 'high' and 'উচ্চ' or overall_intensity == 'moderate' and 'মাঝারি' or 'সহনশীল'} মাত্রায় রয়েছে। "
                f"{coping_desc} "
                f"এটি কোনো ডাক্তারি রোগনির্ণয় নয়, তবে এটি নির্দেশ করে যে একজন সহানুভূতিশীল থেরাপিস্টের সাথে খোলামেলা কথা বলা "
                f"আপনার মানসিক শান্তি ও ভারসাম্যে সাহায্য করতে পারে।"
            )

        elif lang == "hi":
            hi_emotions = {
                "sadness": "उदासी", "anxiety": "चिंता", "anger": "गुस्सा", "fear": "डर",
                "guilt": "अपराधबोध", "shame": "शर्म", "loneliness": "अकेलापन",
                "hopelessness": "निराशा", "overwhelm": "मानसिक थकान व भारीपन", "numbness": "सुन्नपन",
                "joy": "खुशी", "relief": "राहत", "calm": "शांति"
            }
            hi_emo_list = [hi_emotions.get(e, e) for e in dominant_emotions[:3]]
            emo_hi_str = " और ".join(hi_emo_list) if hi_emo_list else "भावनात्मक अनुभव"

            return (
                f"आपके जवाबों के अनुसार, आप वर्तमान में मुख्य रूप से {emo_hi_str} का अनुभव कर रहे हैं, "
                f"जिसकी तीव्रता {overall_intensity == 'high' and 'गंभीर' or overall_intensity == 'moderate' and 'मध्यम' or 'हल्की'} है। "
                f"{coping_desc} "
                f"यह कोई चिकित्सकीय निदान नहीं है, लेकिन यह दर्शाता है कि किसी विशेषज्ञ मनोवैज्ञानिक से बात करना "
                f"आपको भावनात्मक स्पष्टता और सुकून देने में मददगार हो सकता है।"
            )

        else:
            return (
                f"Based on your answers, you seem to be experiencing a mix of {emotions_str}{themes_str}, "
                f"with an overall {overall_intensity} emotional intensity. "
                f"{coping_desc} "
                f"This is not a diagnostic evaluation, but it highlights meaningful areas where exploring your feelings "
                f"with a psychologist or counselor can provide safe, lasting clarity and support."
            )

# Global singleton
emotion_analyzer = EmotionAnalyzer()
