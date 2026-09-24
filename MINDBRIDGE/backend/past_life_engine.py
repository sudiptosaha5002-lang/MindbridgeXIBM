"""
MindBridge Past Life & Life Reflection Question Engine.
Provides multilingual intent detection (English, Hindi, Bengali),
turn-by-turn gentle inquiry sequencing (Short: 6 questions, Full: 13 questions),
voice/text response ingestion, and post-interview Mental State & Emotional Integration Analysis.
"""

import os
import json
import re
import uuid
import time
from typing import Dict, Any, List, Optional, Tuple

class PastLifeEngine:
    """
    Empathetic life reflection engine.
    Guides users through trauma-informed, supportive questions about their past,
    allowing voice and text interaction, and evaluates post-interview mental state.
    """

    # Multilingual Intent Trigger Patterns
    TRIGGER_PATTERNS = {
        "en": [
            r"\b(past\s*life|my\s*past|about\s*my\s*past|childhood\s*memories|growing\s*up|look\s*back\s*at\s*my\s*life|past\s*experiences|past\s*hurts|unresolved\s*past|reflect\s*on\s*my\s*past|questions\s*about\s*past)\b",
            r"\b(tell\s*me\s*about\s*my\s*past|ask\s*me\s*about\s*my\s*past|childhood\s*days|remembering\s*the\s*past)\b"
        ],
        "hi": [
            r"\b(अतीत|बचपन|पुराने\s*दिन|अतीत\s*के\s*बारे\s*में|अतीत\s*के\s*सवाल|बीते\s*हुए\s*कल|पुरानी\s*यादें|बीते\s*दिन)\b",
            r"\b(ateet|bachpan\s*ki\s*yaadein|purani\s*baatein|past\s*ke\s*baare\s*mein|bachpan\s*ke\s*din|purane\s*din)\b"
        ],
        "bn": [
            r"(অতীত|অতীতের\s*কথা|ছোটবেলা|ছোটবেলার\s*স্মৃতি|ছোটবেলার\s*কথা|পুরোনো\s*দিনের\s*কথা|অতীতের\s*অভিজ্ঞতা|অতীতের\s*অনুভূতি|অতীতের\s*প্রশ্ন)"
        ]
    }

    # Sentiments & Keyword Dimensions
    POSITIVE_WORDS = {
        "en": ["happy", "love", "joy", "smile", "warm", "peace", "support", "blessed", "care", "grew", "strong", "gratitude", "safe", "forgive", "healed"],
        "hi": ["खुश", "प्यार", "सुकून", "शांति", "मुस्कान", "मजबूत", "आशीर्वाद", "सुरक्षित", "अपनापन", "उम्मीद", "भरोसा", "माफ", "खुशी", "sahara"],
        "bn": ["আনন্দ", "খুশি", "ভালোবাসা", "শান্তি", "উষ্ণতা", "সাহস", "হাসি", "কৃতজ্ঞতা", "নিরাপদ", "আশা", "স্নেহ", "ক্ষমা", "ভালো"]
    }

    DISTRESS_WORDS = {
        "en": ["sad", "hurt", "trauma", "pain", "lonely", "alone", "cry", "fear", "anxious", "scared", "abuse", "broken", "mistake", "regret", "abandoned", "dark", "guilt"],
        "hi": ["दुख", "दर्द", "अकेला", "चोट", "रोना", "डर", "घबराहट", "पछतावा", "गलती", "टूटा", "तन्हा", "गुस्सा", "khauf", "dard", "udas"],
        "bn": ["কষ্ট", "বেদনা", "দুঃখ", "একাকীত্ব", "ভয়", "কান্না", "আঘাত", "অনুতাপ", "ভুল", "অসহায়", "অন্ধকার", "অশান্তি", "ভাঙা", "অস্থির"]
    }

    RESILIENCE_WORDS = {
        "en": ["learned", "overcome", "survived", "growth", "stronger", "boundary", "boundaries", "trust", "moving on", "wisdom", "progress", "independent"],
        "hi": ["सीखा", "मजबूत", "संभाला", "आगे बढ़ा", "विश्वास", "हिम्मत", "आत्मनिर्भर", "समझदारी", "सबक", "boundary", "himmat"],
        "bn": ["শিখেছি", "মোকাবিলা", "বেড়ে ওঠা", "শক্তিশালী", "সীমানা", "বিশ্বাস", "এগিয়ে যাওয়া", "ধৈর্য", "প্রজ্ঞা", "সাহস", "স্বাবলম্বী"]
    }

    def __init__(self, questions_file: Optional[str] = None):
        if not questions_file:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            questions_file = os.path.join(base_dir, "past_life_questions.json")
        self.questions_file = questions_file
        self.questions: List[Dict[str, Any]] = []
        self.questions_by_id: Dict[int, Dict[str, Any]] = {}
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self._load_questions()

    def _load_questions(self):
        if os.path.exists(self.questions_file):
            try:
                with open(self.questions_file, "r", encoding="utf-8") as f:
                    self.questions = json.load(f)
                    for q in self.questions:
                        self.questions_by_id[q["id"]] = q
            except Exception as e:
                print(f"[PastLifeEngine] Error loading questions: {e}")

    def detect_trigger_intent(self, text: str) -> Optional[str]:
        """
        Scans input text for past life reflection intent.
        Returns detected language code ('en', 'hi', 'bn') if triggered, or None.
        """
        if not text:
            return None
        text_lower = text.lower().strip()

        # Check Bengali first (script-specific)
        for pat in self.TRIGGER_PATTERNS["bn"]:
            if re.search(pat, text):
                return "bn"

        # Check Hindi / Hinglish
        for pat in self.TRIGGER_PATTERNS["hi"]:
            if re.search(pat, text_lower):
                return "hi"

        # Check English
        for pat in self.TRIGGER_PATTERNS["en"]:
            if re.search(pat, text_lower):
                return "en"

        return None

    def get_question_sequence(self, mode: str = "short") -> List[Dict[str, Any]]:
        """Returns ordered question list based on mode ('short' [6 Qs] or 'full' [13 Qs])."""
        if mode == "short":
            return [q for q in self.questions if q.get("is_short_interview", False)]
        return list(self.questions)

    def start_session(
        self,
        user_id: str,
        conversation_id: str,
        language: str = "en",
        mode: str = "short"
    ) -> Dict[str, Any]:
        """
        Initializes a new life reflection interview session.
        """
        # Normalize language
        lang_code = "en"
        lang_lower = (language or "en").lower()
        if "bn" in lang_lower or "bengali" in lang_lower or "bangla" in lang_lower:
            lang_code = "bn"
        elif "hi" in lang_lower or "hindi" in lang_lower or "hinglish" in lang_lower:
            lang_code = "hi"

        seq = self.get_question_sequence(mode)
        session_id = f"pls_{str(uuid.uuid4())[:12]}"

        session = {
            "session_id": session_id,
            "user_id": user_id,
            "conversation_id": conversation_id,
            "language": lang_code,
            "mode": mode,
            "question_ids": [q["id"] for q in seq],
            "current_index": 0,
            "answers": [],
            "status": "in_progress",
            "created_at": time.time(),
            "updated_at": time.time()
        }
        self.active_sessions[session_id] = session

        # Prepare warm opening message and first question
        first_q = seq[0]
        q_text = first_q["question_text"].get(lang_code, first_q["question_text"]["en"])
        gentle_support = first_q["gentle_support"].get(lang_code, first_q["gentle_support"]["en"])
        chips = first_q["suggested_chips"].get(lang_code, first_q["suggested_chips"]["en"])

        welcome_openers = {
            "en": (
                "🌱 **MindBridge Life Reflection Sanctuary**\n\n"
                "Looking back at our past is a tender, courageous journey. "
                "You are in a safe, judgment-free space. You can answer via **voice or text**, "
                "take all the time you need, and skip any question that doesn't feel comfortable.\n\n"
                f"**Question 1 of {len(seq)}**:\n\n"
                f"{q_text}\n\n"
                f"*{gentle_support}*"
            ),
            "bn": (
                "🌱 **মাইন্ডব্রিজ জীবন ও স্মৃতি অনুধ্যান (Life Reflection Sanctuary)**\n\n"
                "অতীতের দিনগুলোর দিকে ফিরে তাকানো এক গভীর সাহস ও মমতার কাজ। "
                "এখানে তুমি সম্পূর্ণ নিরাপদ ও চাপমুক্ত। তুমি **কণ্ঠে (ভয়েস) বা লিখে (টেক্সট)** উত্তর দিতে পারো। "
                "যে কোনো প্রশ্নে দ্বিধা থাকলে নিঃসঙ্কোচে 'Skip' করতে পারো।\n\n"
                f"**প্রশ্ন ১ / {len(seq)}**:\n\n"
                f"{q_text}\n\n"
                f"*{gentle_support}*"
            ),
            "hi": (
                "🌱 **माइंडब्रिज जीवन एवं अतीत संस्मरण (Life Reflection Sanctuary)**\n\n"
                "अपने अतीत और बचपन की यादों को देखना एक बहुत ही आत्मीय और साहसिक कदम है। "
                "यहाँ आप पूरी तरह सुरक्षित और स्वतंत्र हैं। आप **आवाज़ (Voice) या लिखकर (Text)** जवाब दे सकते हैं। "
                "अपनी गति से उत्तर दें और किसी भी सवाल को बेझिझक 'Skip' कर सकते हैं।\n\n"
                f"**सवाल १ / {len(seq)}**:\n\n"
                f"{q_text}\n\n"
                f"*{gentle_support}*"
            )
        }

        return {
            "session_id": session_id,
            "current_index": 0,
            "total_questions": len(seq),
            "language": lang_code,
            "mode": mode,
            "question_id": first_q["id"],
            "question_text": q_text,
            "gentle_support": gentle_support,
            "suggested_chips": chips,
            "formatted_message": welcome_openers.get(lang_code, welcome_openers["en"]),
            "is_complete": False
        }

    def process_answer(
        self,
        session_id: str,
        answer_text: str,
        is_audio: bool = False,
        input_mode: str = "text"
    ) -> Dict[str, Any]:
        """
        Processes the user's answer to the active question, advances to the next question,
        or concludes with a Mental State Analysis if the interview is complete.
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": f"Session '{session_id}' not found or expired.", "is_complete": True}

        lang = session["language"]
        current_idx = session["current_index"]
        q_ids = session["question_ids"]

        if current_idx >= len(q_ids):
            # Already completed
            analysis = self.generate_mental_state_analysis(session)
            return {
                "session_id": session_id,
                "is_complete": True,
                "analysis": analysis,
                "formatted_message": analysis["narrative_report"]
            }

        curr_q_id = q_ids[current_idx]
        curr_q = self.questions_by_id.get(curr_q_id, {})

        # Analyze answer sentiment & themes
        sentiment_score, emotional_themes = self._analyze_answer_text(answer_text, lang)

        # Record answer
        session["answers"].append({
            "question_id": curr_q_id,
            "theme": curr_q.get("theme", "general"),
            "category": curr_q.get("category", ""),
            "question_text": curr_q.get("question_text", {}).get(lang, ""),
            "answer_text": answer_text,
            "is_audio": is_audio,
            "input_mode": input_mode,
            "sentiment_score": sentiment_score,
            "emotional_themes": emotional_themes,
            "timestamp": time.time()
        })

        session["current_index"] += 1
        session["updated_at"] = time.time()
        next_idx = session["current_index"]

        # Generate gentle transitional acknowledgment
        ack_text = self._generate_acknowledgment(answer_text, curr_q, sentiment_score, lang)

        # Check if interview is now complete
        if next_idx >= len(q_ids):
            session["status"] = "completed"
            analysis = self.generate_mental_state_analysis(session)
            
            completion_msg = (
                f"{ack_text}\n\n"
                "---\n\n"
                f"{analysis['narrative_report']}"
            )

            return {
                "session_id": session_id,
                "is_complete": True,
                "current_index": len(q_ids),
                "total_questions": len(q_ids),
                "acknowledgment": ack_text,
                "analysis": analysis,
                "formatted_message": completion_msg,
                "suggested_chips": analysis.get("suggested_chips", [])
            }

        # Present next question
        next_q_id = q_ids[next_idx]
        next_q = self.questions_by_id.get(next_q_id, {})
        next_q_text = next_q["question_text"].get(lang, next_q["question_text"]["en"])
        gentle_support = next_q["gentle_support"].get(lang, next_q["gentle_support"]["en"])
        chips = next_q["suggested_chips"].get(lang, next_q["suggested_chips"]["en"])

        formatted_msg = (
            f"{ack_text}\n\n"
            f"**Question {next_idx + 1} of {len(q_ids)}**:\n\n"
            f"{next_q_text}\n\n"
            f"*{gentle_support}*"
        )

        return {
            "session_id": session_id,
            "is_complete": False,
            "current_index": next_idx,
            "total_questions": len(q_ids),
            "question_id": next_q_id,
            "question_text": next_q_text,
            "gentle_support": gentle_support,
            "suggested_chips": chips,
            "acknowledgment": ack_text,
            "formatted_message": formatted_msg
        }

    def _analyze_answer_text(self, text: str, lang: str) -> Tuple[float, List[str]]:
        """
        Computes polarity score (-1.0 to +1.0) and detects psychological markers.
        """
        if not text:
            return 0.0, ["neutral"]

        text_lower = text.lower()
        pos_words = self.POSITIVE_WORDS.get(lang, self.POSITIVE_WORDS["en"])
        distress_words = self.DISTRESS_WORDS.get(lang, self.DISTRESS_WORDS["en"])
        resilience_words = self.RESILIENCE_WORDS.get(lang, self.RESILIENCE_WORDS["en"])

        pos_count = sum(1 for w in pos_words if w in text_lower)
        distress_count = sum(1 for w in distress_words if w in text_lower)
        resil_count = sum(1 for w in resilience_words if w in text_lower)

        themes = []
        if pos_count > 0:
            themes.append("warmth_and_fondness")
        if distress_count > 0:
            themes.append("processing_vulnerability")
        if resil_count > 0:
            themes.append("resilience_and_growth")
        if not themes:
            themes.append("reflective_neutral")

        total = pos_count + distress_count + resil_count
        if total == 0:
            return 0.1, themes

        score = (pos_count + (resil_count * 0.8) - (distress_count * 1.2)) / total
        score = max(-1.0, min(1.0, score))
        return score, themes

    def _generate_acknowledgment(self, user_answer: str, question: Dict[str, Any], score: float, lang: str) -> str:
        """Generates validating and compassionate bridge phrases between turns."""
        is_skip = "skip" in user_answer.lower() or "পরের" in user_answer or "अगले" in user_answer

        if lang == "bn":
            if is_skip:
                return "অবশ্যই, তোমার সিদ্ধান্তকে পূর্ণ সম্মান জানাই। চলো পরবর্তী অংশে এগিয়ে যাই..."
            if score < -0.2:
                return "তোমার এই অনুভূতি ভাগ করে নেওয়ার জন্য অনেক ধন্যবাদ। অতীতের কঠিন স্মৃতি বয়ে বেড়ানো সত্যিই অনেক ভারাক্রান্ত করে, কিন্তু তুমি অত্যন্ত সাহসের সাথে তা ব্যক্ত করেছো।"
            elif score > 0.3:
                return "তোমার এই মধুর স্মৃতির কথা শুনে মনটা খুব শান্ত ও আনন্দে ভরে উঠলো। এই সুন্দর মুহূর্তগুলো আমাদের ভেতরের শক্তিকে উজ্জ্বল রাখে।"
            else:
                return "তোমার গভীর অনুভূতির কথাটি আমি মনোযোগ দিয়ে শুনলাম। নিজের জীবনের প্রতি এই সচেতন দৃষ্টিভঙ্গি সত্যিই প্রশংসনীয়।"

        elif lang == "hi":
            if is_skip:
                return "बिल्कुल, आपकी पसंद का पूरा सम्मान है। चलिए अगले सवाल की ओर बढ़ते हैं..."
            if score < -0.2:
                return "अपनी इस बात को इतने खुले दिल से साझा करने के लिए धन्यवाद। अतीत के कठिन पलों को याद करना आसान नहीं होता, पर आपकी यह ईमानदारी आपके साहस को दर्शाती है।"
            elif score > 0.3:
                return "आपकी यह सुखद और प्यारी याद सुनकर दिल को बहुत सुकून मिला। ऐसे खूबसूरत पल हमारे भीतर एक सकारात्मक ऊर्जा भर देते हैं।"
            else:
                return "आपकी बात को मैंने बहुत ध्यान और आत्मीयता से सुना। अपने जीवन के पन्नों को इतनी समझदारी से देखना सचमुच सराहनीय है।"

        else: # en
            if is_skip:
                return "Understood completely. Honoring your boundaries is wonderful. Let's move gently to the next step..."
            if score < -0.2:
                return "Thank you for trusting me with this tender experience. Acknowledging difficult parts of our journey takes immense courage, and I'm right here with you."
            elif score > 0.3:
                return "What a heartwarming and nourishing memory. Moments like these serve as beautiful golden threads in our life tapestry."
            else:
                return "I hear you deeply. Reflecting on these formative chapters with such clarity shows profound self-awareness."

    def generate_mental_state_analysis(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesizes all user responses into a holistic, empathetic Mental State Report.
        """
        answers = session.get("answers", [])
        lang = session.get("language", "en")
        mode = session.get("mode", "short")

        if not answers:
            return {
                "overall_state": "Incomplete Session",
                "narrative_report": "No answers were recorded during this reflection.",
                "dimensions": {}
            }

        # Calculate psychological dimension indices
        avg_sentiment = sum(a.get("sentiment_score", 0.0) for a in answers) / max(1, len(answers))
        
        all_themes = []
        for a in answers:
            all_themes.extend(a.get("emotional_themes", []))

        # 1. Nostalgia & Emotional Warmth Index (0 to 100)
        warmth_hits = sum(1 for t in all_themes if t == "warmth_and_fondness")
        nostalgia_index = int(min(100, max(20, (warmth_hits / max(1, len(answers))) * 85 + (avg_sentiment * 15) + 30)))

        # 2. Resilience & Growth Index (0 to 100)
        resil_hits = sum(1 for t in all_themes if t == "resilience_and_growth")
        resilience_index = int(min(100, max(25, (resil_hits / max(1, len(answers))) * 80 + 35)))

        # 3. Emotional Processing Need / Load (Low, Moderate, High)
        vuln_hits = sum(1 for t in all_themes if t == "processing_vulnerability")
        if vuln_hits >= 3 or avg_sentiment < -0.35:
            processing_load = "Tender / Needs Gentle Processing"
            load_color = "#f59e0b"
        elif vuln_hits >= 1:
            processing_load = "Moderate / Healthy Processing"
            load_color = "#3b82f6"
        else:
            processing_load = "Integrated / Grounded"
            load_color = "#10b981"

        # 4. Relational Trust & Openness Index (0 to 100)
        trust_index = int(min(100, max(30, 60 + (avg_sentiment * 25) + (resil_hits * 5))))

        # Primary Emotional Archetype
        if avg_sentiment > 0.3:
            archetype_en = "Warm, Grounded & Nostalgic"
            archetype_bn = "উষ্ণ, শান্ত ও স্মৃতিমধুর"
            archetype_hi = "सकारात्मक, आत्मीय और सुकून भरा"
        elif resil_hits >= 2:
            archetype_en = "Resilient & Meaning-Seeking"
            archetype_bn = "সাহসী, সহনশীল ও সম্ভাবনাময়"
            archetype_hi = "साहसी, जुझारू और समझदार"
        elif vuln_hits >= 2:
            archetype_en = "Vulnerable & Healing"
            archetype_bn = "সংবেদনশীল ও আরোগ্যকামী"
            archetype_hi = "संवेदनशील और उपचारात्मक"
        else:
            archetype_en = "Reflective & Introspective"
            archetype_bn = "গভীর আত্মসচেতন ও চিন্তাশীল"
            archetype_hi = "गंभीर, आत्म-चिंतनशील और संतुलित"

        archetypes = {"en": archetype_en, "bn": archetype_bn, "hi": archetype_hi}
        primary_archetype = archetypes.get(lang, archetype_en)

        # Generate comprehensive narrative report in target language
        if lang == "bn":
            narrative = (
                f"### 🪷 **জীবন অনুধ্যান ও মানসিক অবস্থা বিশ্লেষণ (Life Reflection Report)**\n\n"
                f"**বর্তমান মানসিক স্থিতি:** **{primary_archetype}**\n\n"
                f"তোমার অতীতের স্মৃতি ও অনুভূতির গভীরতা উন্মোচনের মধ্য দিয়ে একটি চমৎকার আত্মদর্শন সম্পন্ন হলো। নিচে তোমার মনের ভেতরের শক্তি ও সমন্বয়ের একটি সূক্ষ্ম চিত্র তুলে ধরা হলো:\n\n"
                f"• **নস্টালজিয়া ও মধুর স্মৃতির সংযোগ:** `{nostalgia_index}/100` — ছোটবেলার সুখের মুহূর্তগুলো আজও তোমার মনে প্রশান্তি জোগায়।\n"
                f"• **মানসিক সহনশীলতা ও প্রজ্ঞা (Resilience):** `{resilience_index}/100` — অতীতের অভিজ্ঞতা থেকে শিখে এগিয়ে চলার সুন্দর সামর্থ্য রয়েছে।\n"
                f"• **সম্পর্কের বিশ্বাস ও খোলামেলা ভাব:** `{trust_index}/100` — মানুষের সাথে খাঁটি ও অর্থপূর্ণ সম্পর্ক গড়ার সচেতনতা লক্ষণীয়।\n"
                f"• **মানসিক ভারমোচন অবস্থা:** **{processing_load}**\n\n"
                f"🌿 **মমতাময় পর্যবেক্ষণ ও পরামর্শ:**\n"
                f"তুমি যেভাবে তোমার অতীতকে সততা ও অনুভূতির সাথে আলিঙ্গন করেছো, তা অত্যন্ত প্রশংসনীয়। যে কথাগুলো কষ্ট দেয়, সেগুলোকে জোর করে আটকে না রেখে প্রতিদিন কয়েক মিনিট শান্ত শ্বাসক্রিয়া (৪-৭-৮ প্রাণায়াম) বা নিজের সাথে ডায়েরিতে কথা বলার অভ্যাস রাখলে মনে গভীর স্বস্তি বজায় থাকবে।"
            )
            chips = ["৪-৭-৮ শান্ত শ্বাসক্রিয়া শুরু করি", "বিশেষজ্ঞের সাথে কথা বলতে চাই", "আরেকটি প্রশ্নাবলি করি", "ধন্যবাদ, আমি ভালো আছি"]

        elif lang == "hi":
            narrative = (
                f"### 🪷 **जीवन संस्मरण एवं मानसिक स्थिति विश्लेषण (Life Reflection Report)**\n\n"
                f"**वर्तमान मानसिक स्थिति का स्वरूप:** **{primary_archetype}**\n\n"
                f"अपने अतीत के पन्नों को इतनी आत्मीयता और ईमानदारी से देखने के लिए आपका धन्यवाद। आपके उत्तरों के आधार पर आपकी भावनात्मक ऊर्जा का एक विस्तृत विश्लेषण प्रस्तुत है:\n\n"
                f"• **नॉस्टैल्जिया एवं सुखद यादों का जुड़ाव:** `{nostalgia_index}/100` — बचपन के सुकून भरे पल आज भी आपके मन को संबल देते हैं।\n"
                f"• **सहनशीलता एवं आंतरिक विकास (Resilience):** `{resilience_index}/100` — मुश्किलों से सीखकर आगे बढ़ने की एक मजबूत क्षमता।\n"
                f"• **रिश्तों में विश्वास और आत्मीयता:** `{trust_index}/100` — गहरे और सच्चे रिश्तों की ओर आपका सकारात्मक दृष्टिकोण।\n"
                f"• **भावनात्मक भार की स्थिति:** **{processing_load}**\n\n"
                f"🌿 **आत्मीय मार्गदर्शन एवं सुझाव:**\n"
                f"अपने अतीत को बिना किसी अपराधबोध के स्वीकार करना आत्म-विकास का सबसे बड़ा उपहार है। कठिन यादों के समय अपनी सीमाओं का ध्यान रखें। प्रतिदिन ३ मिनट गहरी सांसों का अभ्यास और माइंडब्रिज के शांति संगीत का आनंद आपको और अधिक संतुलित रखेगा।"
            )
            chips = ["४-७-८ शांत प्राणायाम करें", "काउंसलर से परामर्श लें", "शांति संगीत सुनें", "धन्यवाद, अच्छा महसूस हो रहा है"]

        else: # English
            narrative = (
                f"### 🪷 **MindBridge Life Reflection & Mental State Synthesis**\n\n"
                f"**Dominant Emotional Landscape:** **{primary_archetype}**\n\n"
                f"Thank you for exploring your past with such vulnerability and grace. Here is your holistic psychological reflection and integration profile:\n\n"
                f"• **Nostalgia & Emotional Warmth:** `{nostalgia_index}/100` — Your capacity to draw comfort and grounding from meaningful memories.\n"
                f"• **Resilience & Meaning-Making:** `{resilience_index}/100` — Demonstrated ability to extract wisdom and boundaries from formative hardships.\n"
                f"• **Relational Trust & Connectedness:** `{trust_index}/100` — Balanced awareness in nurturing authentic, psychologically safe bonds.\n"
                f"• **Emotional Processing Load:** **{processing_load}**\n\n"
                f"🌿 **Therapeutic Observations & Gentle Next Steps:**\n"
                f"Your reflection reveals a healthy balance between holding space for tender memories and actively shaping who you want to be today. "
                f"Consider journaling whenever recurring past thoughts arise, and honor the boundaries you have built. You are worthy of peace and growth."
            )
            chips = ["Practice 4-7-8 Breathing", "Explore Therapist Directory", "Listen to Calming Soundscape", "Save This Reflection"]

        return {
            "primary_archetype": primary_archetype,
            "nostalgia_index": nostalgia_index,
            "resilience_index": resilience_index,
            "trust_index": trust_index,
            "processing_load": processing_load,
            "load_color": load_color,
            "narrative_report": narrative,
            "suggested_chips": chips,
            "total_answered": len(answers),
            "interview_mode": mode
        }

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.active_sessions.get(session_id)


# Global singleton instance
past_life_engine = PastLifeEngine()
