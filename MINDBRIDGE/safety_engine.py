import re

class CrisisSafetyFilter:
    def __init__(self):
        # Deterministic multi-script crisis lexicons
        self.lexicons = {
            "ACTIVE_SUICIDE_INTENT": [
                "kill myself", "end my life", "suicide", "want to die", "no reason to live", "want to end it all", "don't want to live",
                "मरना चाहता", "आत्महत्या", "जिंदगी खत्म", "मरने का मन", "जीने की इच्छा नहीं", "खुदकुशी",
                "marna chahta", "marne ka man", "zindagi khatam", "khudkushi", "end everything",
                "মরে যেতে চাই", "বেঁচে থেকে লাভ নেই", "আত্মহত্যা", "নিজের জীবন শেষ",
                "more jete chai", "beche theke labh nei", "suicide korbo", "jibon shesh", "amake mere feli"
            ],
            "IMMEDIATE_SELF_HARM": [
                "cut myself", "hurt myself", "cutting my wrists", "cut my wrist", "slitting",
                "खुद को चोट", "नस काट", "हाथ काट",
                "khud ko chot", "nas kaat", "haath kaat", "khoon nikal",
                "নিজেকে আঘাত", "হাত কাট", "রক্ত বেরোচ্ছে",
                "nijeke aghat", "haat kat", "rokto berochhe", "nijeke kosto dibo"
            ],
            "HARM_TO_OTHERS": [
                "kill him", "kill her", "murder", "stab someone", "shoot them",
                "उसको मार दूँगा", "जान से मार", "कत्ल कर", "गोली मार",
                "usko maar dunga", "jaan se maar", "goli maar", "katl",
                "ওকে মেরে ফেলবো", "খুন করবো", "গুলি করবো",
                "oke mere felbo", "khun korbo", "guli korbo"
            ],
            "MEDICAL_EMERGENCY": [
                "took pills", "too many pills", "overdose", "swallowed too many", "can't breathe", "passing out", "drank poison", "bleeding out",
                "गोलियां खा ली", "जहर पी लिया", "सांस नहीं आ रही", "ओवरडोज़",
                "goliyan kha li", "pills kha liye", "zeher pi", "saans nahi aa rahi", "behosh",
                "অনেক ওষুধ খেয়েছি", "বিষ খেয়েছি", "নিঃশ্বাস বন্ধ", "ওভারডোজ",
                "onek osudh kheyechi", "bish kheyechi", "nishash bondho", "behosh hoye jachi", "pil kheyechi"
            ]
        }
        
        # Compile fallback regex patterns for highly optimized string matching (O(N) traversal over text)
        self.compiled_patterns = {}
        for category, phrases in self.lexicons.items():
            escaped_phrases = [re.escape(p.lower()) for p in phrases]
            pattern = "|".join(escaped_phrases)
            self.compiled_patterns[category] = re.compile(pattern, re.IGNORECASE)

    def evaluate_safety(self, text: str, detected_lang: str = "en") -> dict:
        """
        Evaluates text for crisis triggers natively without external ML APIs.
        Returns a structured dictionary indicating risk level and payload actions.
        """
        text_lower = text.lower()
        
        for category, pattern in self.compiled_patterns.items():
            match = pattern.search(text_lower)
            if match:
                matched_term = match.group(0)
                return {
                    "triggered": True,
                    "risk_category": category,
                    "severity": "CRITICAL",
                    "matched_term": matched_term,
                    "action_required": "ACTIVATE_EMERGENCY_MODE",
                    "emergency_payload": {
                        "message": "Immediate help is available. Please reach out to emergency services right now.",
                        "helpline_india": "112 / 9152987821 (AASRA)",
                        "helpline_bd": "999 / Kaan Pete Roi (01779554391)",
                        "prompt": "We strongly encourage you to call a trusted contact or emergency services."
                    }
                }
                
        # Clean text
        return {
            "triggered": False,
            "risk_category": "NONE",
            "severity": "ROUTINE",
            "matched_term": None,
            "action_required": "CONTINUE",
            "emergency_payload": None
        }
