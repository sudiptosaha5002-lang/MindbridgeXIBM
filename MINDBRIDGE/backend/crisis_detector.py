import re
import json
import os
from typing import Dict, Any

# Crisis and safety lexical patterns
CRISIS_PATTERNS = {
    "immediate": {
        "suicidal_feelings": [
            r"\b(suicid|kill\s*myself|end\s*my\s*life|want\s*to\s*die|don'?t\s*want\s*to\s*live|no\s*reason\s*to\s*live|better\s*off\s*dead|end\s*it\s*all)\b",
            r"\b(mar\s*jana\s*chahta|jaan\s*dena|khudkushi|aatmhatya|zindagi\s*khatam)\b",
            r"(আত্মহত্যা|মরতে\s*চাই|বেঁচে\s*থাকার\s*ইচ্ছে\s*নেই|জীবন\s*শেষ)"
        ],
        "self_harm_thoughts": [
            r"\b(self\s*harm|harm\s*myself|cutting\s*myself|slit\s*my|burn\s*myself|hurt\s*myself|punish\s*myself|plan\s*to\s*hurt)\b",
            r"\b(khud\s*ko\s*chot|apne\s*aap\s*ko\s*nuksan)\b",
            r"(নিজের\s*ক্ষতি|হাত\s*কাটা|নিজেকে\s*আঘাত)"
        ],
        "harm_to_others": [
            r"\b(kill\s*someone|hurt\s*someone|murder)\b",
            r"\b(kisi\s*ko\s*maar|jaan\s*se\s*maar)\b",
            r"(কাউকে\s*হত্যা|খুন)"
        ]
    },
    "high": {
        "intense_emotional_pain": [
            r"\b(unbearable\s*pain|pain\s*is\s*too\s*much|broken\s*inside|shattered|can'?t\s*take\s*this\s*anymore|suffocating\s*inside)\b",
            r"\b(bahut\s*dard|bardasht\s*nahi\s*hota|andar\s*se\s*tut\s*gaya|dil\s*bahut\s*ro\s*raha)\b",
            r"(অসহ্য\s*যন্ত্রণা|ভেতরটা\s*ভেঙে\s*গেছে|আর\s*সহ্য\s*হচ্ছে\s*না|বুক\s*ভেঙে\s*যাচ্ছে)"
        ]
    },
    "moderate": {
        "trauma_reference": [
            r"\b(trauma|ptsd|flashback|abused|assaulted|horrible\s*memory|violated|molested|assault)\b",
            r"\b(purani\s*burii\s*yaad|hadsah|trauma|shoshan)\b",
            r"(ট্রমা|অতীতের\s*ভয়াবহ\s*স্মৃতি|নির্যাতিত|নিপীড়ন)"
        ]
    }
}

class CrisisDetector:
    """
    Independent emergency and safety detector.
    Runs BEFORE normal emotion classification.
    """
    
    def __init__(self):
        self.patterns = CRISIS_PATTERNS

    def check_crisis(self, text: str) -> Dict[str, Any]:
        """
        Scans text for immediate, high, or moderate crisis patterns.
        """
        clean_text = (text or "").strip().lower()
        if not clean_text:
            return {
                "risk_flag": "none",
                "matched_themes": [],
                "requires_crisis_flow": False
            }

        matched_themes = []
        highest_risk = "none"

        # Check in order of severity
        for risk_level in ["immediate", "high", "moderate"]:
            for theme, regex_list in self.patterns[risk_level].items():
                for pat in regex_list:
                    if re.search(pat, clean_text):
                        if theme not in matched_themes:
                            matched_themes.append(theme)
                        if highest_risk == "none" or (highest_risk == "moderate" and risk_level in ["high", "immediate"]) or (highest_risk == "high" and risk_level == "immediate"):
                            highest_risk = risk_level

        requires_crisis_flow = highest_risk in ["immediate", "high"]

        return {
            "risk_flag": highest_risk,
            "matched_themes": matched_themes,
            "requires_crisis_flow": requires_crisis_flow,
            "action": "activate_crisis_flow" if requires_crisis_flow else "continue_normal_screening"
        }

# Global singleton
crisis_detector = CrisisDetector()
