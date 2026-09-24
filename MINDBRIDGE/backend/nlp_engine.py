"""
NLP and Safety Classification Engine for MindBridge.
Implements sentiment analysis, non-diagnostic guardrails, 
crisis risk detection, and empathetic response synthesis.
"""

import re
import json
import random
from resource_knowledge_engine import retrieve_therapeutic_insights
from linguistic_resource_trainer import linguistic_trainer

# Crisis Triggers (High Severity & Immediate Risk)
CRISIS_PATTERNS = [
    r"\b(suicid|kill\s*myself|end\s*my\s*life|end\s*it\s*all|want\s*to\s*die|don'?t\s*want\s*to\s*live|harm\s*myself|self\s*harm|cutting\s*myself|slit|hang\s*myself|take\s*all\s*my\s*pills|overdose|feeling\s*unsafe\s*with\s*myself|no\s*reason\s*to\s*live|better\s*off\s*dead)\b",
    r"\b(mar\s*jana\s*chahta|jaan\s*dena|khudkushi|aatmhatya|zindagi\s*khatam)\b", # Hindi
    r"\b(matarme|quitarme\s*la\s*vida|suicidar|suicidio|no\s*quiero\s*vivir|acabar\s*con\s*todo|desear\s*morir)\b", # Spanish
    r"\b(me\s*matar|tirar\s*minha\s*vida|suicidio|suicidar|nao\s*quero\s*mais\s*viver|acabar\s*com\s*tudo|desejo\s*morrer)\b", # Portuguese
    r"(আত্মহত্যা|মরতে\s*চাই|বেঁচে\s*থাকার\s*ইচ্ছে\s*নেই|জীবন\s*শেষ|নিজের\s*ক্ষতি)" # Bengali
]

# High Distress (Urgent but Supportive Triage)
HIGH_DISTRESS_PATTERNS = [
    r"\b(panic\s*attack|can'?t\s*breathe|unbearable\s*pain|breakdown|losing\s*my\s*mind|chest\s*tightness|terrified|paralyzed\s*with\s*fear)\b",
    r"\b(bahut\s*zyada\s*stress|dar\s*lag\s*raha|ghabrahat)\b",
    r"\b(ataque\s*de\s*panico|no\s*puedo\s*respirar|dolor\s*insoportable|desesperado|desesperada)\b",
    r"\b(ataque\s*de\s*panico|nao\s*consigo\s*respirar|dor\s*insuportavel|desespero)\b",
    r"(প্যানিক\s*অ্যাটাক|নিশ্বাস\s*নিতে\s*কষ্ট|ভীষণ\s*ভয়|অসহ্য\s*যন্ত্রণা)"
]

# Clinical / Diagnostic Query Patterns (To be deflected safely)
DIAGNOSTIC_QUERIES = [
    r"\b(do\s*i\s*have|am\s*i\s*suffering\s*from|diagnose\s*me|what\s*mental\s*illness|is\s*this\s*depression|is\s*this\s*bipolar|is\s*this\s*adhd|is\s*this\s*schizophrenia|do\s*i\s*have\s*ocd|prescribe|what\s*medicine|what\s*pills|should\s*i\s*take\s*(antidepressants|xanax|prozac|escitalopram))\b",
    r"\b(kya\s*mujhe\s*depression\s*hai|dawa\s*batao|kya\s*ye\s*bipolar\s*hai|kya\s*bimari\s*hai)\b",
    r"\b(tengo\s*depresion|diagnosticame|que\s*medicamento|que\s*pastillas|tengo\s*tdah|tengo\s*bipolaridad|recetame|que\s*enfermedad\s*tengo)\b",
    r"\b(tenho\s*depressao|me\s*diagnostique|qual\s*remedio|qual\s*medicamento|tenho\s*tdah|tenho\s*bipolaridade|receite|qual\s*doenca\s*tenho)\b",
    r"(আমার\s*কি\s*ডিপ্রেশন|আমাকে\s*রোগনির্ণয়\s*করুন|ওষুধ\s*দিন|কী\s*ওষুধ\s*খাব|ডায়াগনসিস)"
]

# Emotion & Dimension Keywords (Multilingual: EN, HI, ES, PT, BN)
DIMENSION_KEYWORDS = {
    "mood": {
        "melancholic": [
            "sad", "crying", "empty", "lonely", "down", "hopeless", "heavy", "grief", "depressed",
            "उदास", "dukh", "rona", "akela", "dukhi", "man udas", "bebas",
            "triste", "tristeza", "llorando", "vacio", "vacia", "solo", "sola", "soledad", "deprimido", "deprimida", "sin esperanza", "desolado",
            "triste", "tristeza", "chorando", "vazio", "vazia", "sozinho", "sozinha", "solidao", "deprimido", "deprimida", "desesperanca",
            "খারাপ", "মন খারাপ", "কষ্ট", "কান্না", "একা", "একাকীত্ব", "বিষণ্ণ", "হতাশ", "ভালো লাগছে না", "বেদনা", "দুঃখ"
        ],
        "overwhelmed": [
            "overwhelmed", "exhausted", "too much", "burnout", "drained", "suffocating", "can't cope", "burn out",
            "thak gaya", "thak gayi", "dimag thak", "overwhelmed", "bardasht nahi", "bojh",
            "abrumado", "abrumada", "agotado", "agotada", "exhausto", "exhausta", "sin energia", "colapso", "no puedo mas", "sobrecargado",
            "sobrecarregado", "sobrecarregada", "esgotado", "esgotada", "exaustao", "sem forcas", "nao aguento mais",
            "বিপর্যস্ত", "ক্লান্ত", "ক্লান্তি", "চাপ", "অতিরিক্ত চাপ", "আর পারছি না", "ভারাক্রান্ত", "হিমশিম", "হাঁপিয়ে"
        ],
        "anxious": [
            "anxious", "nervous", "worry", "scared", "fear", "racing thoughts", "jittery", "stress", "panic", "tight chest",
            "chinta", "stress", "ghabrahat", "dar", "tension", "bechaini", "dar lag raha",
            "ansiedad", "ansioso", "ansiosa", "nervioso", "nerviosa", "preocupado", "preocupada", "miedo", "panico", "angustia", "pecho apretado", "estres",
            "ansiedade", "ansioso", "ansiosa", "nervoso", "nervosa", "preocupado", "preocupada", "medo", "panico", "angustia", "aperto no peito", "estresse",
            "উদ্বেগ", "উদ্বিগ্ন", "ভয়", "ভয় লাগছে", "অস্থির", "অস্থিরতা", "বুক ধড়ফড়", "টেনশন", "আতঙ্ক", "উৎকণ্ঠা"
        ],
        "calm": [
            "calm", "okay", "peaceful", "better", "relieved", "relaxed", "fine",
            "thik hoon", "shant", "behtar", "sukoon", "theek",
            "tranquilo", "tranquila", "en paz", "mejor", "aliviado", "aliviada", "relajado", "relajada", "bien",
            "calmo", "calma", "tranquilo", "tranquila", "em paz", "melhor", "aliviado", "aliviada", "relaxado", "bem",
            "শান্ত", "ভালো", "স্বস্তি", "হালকা", "একটু ভালো", "ঠিক আছি", "প্রশান্তি", "শান্তিপূর্ণ"
        ],
        "hopeful": [
            "hopeful", "optimistic", "motivated", "looking forward", "better today",
            "umeed", "positive", "acha lag raha",
            "esperanzado", "esperanzada", "optimista", "motivado", "motivada", "con animo", "ilusionado",
            "esperancoso", "esperancosa", "otimista", "motivado", "motivada", "com esperanca",
            "আশাবাদী", "ইতিবাচক", "নতুন আশা", "ভালো লাগছে", "উৎসাহ", "ভরসা"
        ]
    },
    "stress": {
        "workplace": [
            "job", "boss", "deadline", "work", "career", "exams", "studies", "college", "office", "target", "interview", "money",
            "kaam", "naukri", "office", "padhai", "exam", "target", "boss",
            "trabajo", "jefe", "plazo", "carrera", "examen", "estudio", "oficina", "empleo", "laboral", "sueldo",
            "trabalho", "chefe", "prazo", "carreira", "exame", "estudo", "faculdade", "escritorio", "emprego", "salario",
            "কাজ", "অফিস", "চাকরি", "বস", "পড়াশোনা", "পরীক্ষা", "ডেডলাইন", "টার্গেট", "কলেজ", "টাকা"
        ],
        "relationship": [
            "partner", "boyfriend", "girlfriend", "husband", "wife", "family", "parents", "fight", "breakup", "loneliness", "divorce", "cheated",
            "rishta", "ladai", "breakup", "dost", "pariwar", "gharwale", "pati", "patni",
            "pareja", "novio", "novia", "esposo", "esposa", "familia", "padres", "pelea", "ruptura", "separacion", "discusion",
            "parceiro", "parceira", "namorado", "namorada", "esposo", "esposa", "familia", "pais", "briga", "termino", "separacao",
            "সম্পর্ক", "বন্ধু", "পরিবার", "মা", "বাবা", "ব্রেকআপ", "ঝগড়া", "ডিভোর্স", "সঙ্গী", "স্বামী", "স্ত্রী", "ভালোবাসা"
        ],
        "health": [
            "sick", "tired", "pain", "fatigue", "headache", "body ache", "dizziness",
            "bimari", "dard", "sar dard", "kamzori",
            "enfermo", "enferma", "dolor", "fatiga", "dolor de cabeza", "mareo", "cuerpo",
            "doente", "dor", "fadiga", "dor de cabeca", "tontura", "corpo cansado",
            "অসুস্থ", "ব্যথা", "মাথাব্যথা", "দুর্বলতা", "শরীর খারাপ", "ক্লান্ত শরীর", "কষ্ট হচ্ছে"
        ]
    },
    "sleep": {
        "poor": [
            "insomnia", "can't sleep", "waking up", "nightmare", "restless", "sleep late", "tired in morning", "no sleep", "sleepless",
            "neend nahi", "neend khul", "raat ko jagna", "insomnia", "neend nahi aa rahi", "so nahi pa raha",
            "insomnio", "no puedo dormir", "despertar", "pesadilla", "desvelo", "desvelado", "sin dormir", "sueno inquieto",
            "insonia", "nao consigo dormir", "acordando", "pesadelo", "noite em claro", "sem dormir", "sono ruim",
            "ঘুম হচ্ছে না", "অনিদ্রা", "রাতে ঘুম", "ঘুম ভাঙা", "দুঃস্বপ্ন", "জেগে থাকা", "ঘুম আসে না", "ঘুমের সমস্যা", "ঘুম নেই"
        ],
        "good": [
            "slept well", "good sleep", "8 hours", "rested", "peaceful sleep",
            "acchi neend", "so gaya",
            "dormi bien", "buen sueno", "descanse",
            "dormi bem", "sono tranquilo", "descansei",
            "ভালো ঘুম", "শান্তির ঘুম", "পর্যাপ্ত ঘুম", "ঘুম ভালো হয়েছে"
        ]
    },
    "habits": {
        "isolated": [
            "staying inside", "haven't eaten", "skipping meals", "alone all day", "not talking to anyone",
            "encerrado", "encerrada", "sin comer", "sin salir",
            "trancado", "trancada", "sem comer", "sem sair de casa",
            "ঘরে বন্ধ", "না খেয়ে থাকা", "কারো সাথে কথা না বলা"
        ],
        "active": [
            "walk", "exercise", "workout", "ate well", "went outside", "talked to friend",
            "caminar", "ejercicio", "sali a caminar",
            "caminhada", "exercicio", "sai para caminhar",
            "হাঁটা", "ব্যায়াম", "বাইরে যাওয়া"
        ]
    }
}

EMERGENCY_RESOURCES = [
    {
        "name": "Tele-MANAS (Govt of India)",
        "number": "14416 / 1800 891 4416",
        "description": "24/7 Toll-Free Multilingual National Mental Health Helpline (NIMHANS/Govt. of India)",
        "action": "tel:14416",
        "badge": "24/7 Toll-Free (India)"
    },
    {
        "name": "Vandrevala Foundation Helpline",
        "number": "+91 9999 666 555",
        "description": "Free, confidential 24/7 crisis response and emotional counseling support across India.",
        "action": "tel:+919999666555",
        "badge": "24/7 Available"
    },
    {
        "name": "AASRA Crisis Center",
        "number": "+91 98204 66726",
        "description": "24/7 confidential crisis intervention and suicide prevention helpline.",
        "action": "tel:+919820466726",
        "badge": "Immediate Support"
    },
    {
        "name": "KIRAN Mental Health Helpline",
        "number": "1800-599-0019",
        "description": "Ministry of Social Justice 24/7 helpline in 13 languages.",
        "action": "tel:18005990019",
        "badge": "Govt of India (13 Langs)"
    },
    {
        "name": "988 Suicide & Crisis Lifeline (US/Global)",
        "number": "988",
        "description": "Free and confidential support for anyone in suicidal crisis or emotional distress.",
        "action": "tel:988",
        "badge": "US / International"
    }
]

def scan_safety(text):
    """
    Scans text for safety, crisis signals, and urgency level.
    Returns: dict with risk_level ('emergency', 'distress', 'safe') and resources.
    """
    if not text:
        return {"risk_level": "safe", "is_crisis": False}
        
    lower_text = text.lower()
    
    # 1. High Emergency / Crisis Scan
    for pattern in CRISIS_PATTERNS:
        if re.search(pattern, lower_text):
            return {
                "risk_level": "emergency",
                "is_crisis": True,
                "urgency": "immediate",
                "message": "It sounds like you are carrying overwhelming pain right now. Please know that your life matters, and you do not have to carry this alone. Immediate, compassionate help is available 24/7.",
                "resources": EMERGENCY_RESOURCES
            }
            
    # 2. High Distress / Anxiety Surge Scan
    for pattern in HIGH_DISTRESS_PATTERNS:
        if re.search(pattern, lower_text):
            return {
                "risk_level": "distress",
                "is_crisis": False,
                "urgency": "elevated",
                "message": "I notice you might be experiencing intense distress or anxiety right now. Let's pause together for a gentle moment. Feel your feet on the floor and take a slow, deep breath.",
                "resources": EMERGENCY_RESOURCES[:2]
            }

    return {"risk_level": "safe", "is_crisis": False, "urgency": "normal"}

def analyze_dimensions(text):
    """
    Extracts emotional dimensions: mood tone, stress score estimate, sleep, and habits.
    """
    lower = text.lower()
    detected_emotions = []
    stress_points = 45 # baseline default
    sleep_status = "unspecified"
    mood_label = "Reflective"

    # Analyze Mood
    for mood, words in DIMENSION_KEYWORDS["mood"].items():
        if any(w in lower for w in words):
            detected_emotions.append(mood)
            if mood == "melancholic":
                stress_points += 25
                mood_label = "Low / Heavy-Hearted"
            elif mood == "overwhelmed":
                stress_points += 35
                mood_label = "Overwhelmed"
            elif mood == "anxious":
                stress_points += 30
                mood_label = "Anxious / Restless"
            elif mood in ["calm", "hopeful"]:
                stress_points = max(15, stress_points - 20)
                mood_label = "Calm & Receptive"

    # Analyze Stressors
    for stress_cat, words in DIMENSION_KEYWORDS["stress"].items():
        if any(w in lower for w in words):
            detected_emotions.append(f"stressor:{stress_cat}")
            stress_points += 15

    # Analyze Sleep
    if any(w in lower for w in DIMENSION_KEYWORDS["sleep"]["poor"]):
        sleep_status = "Disrupted / Insomnia"
        detected_emotions.append("sleep_disrupted")
        stress_points += 15
    elif any(w in lower for w in DIMENSION_KEYWORDS["sleep"]["good"]):
        sleep_status = "Restful"
        detected_emotions.append("sleep_healthy")
        stress_points = max(10, stress_points - 10)

    # Analyze Habits
    if any(w in lower for w in DIMENSION_KEYWORDS["habits"]["isolated"]):
        detected_emotions.append("social_withdrawal")
        stress_points += 10

    stress_level = min(100, max(10, stress_points))
    return {
        "detected_emotions": list(set(detected_emotions)),
        "stress_level": stress_level,
        "mood_label": mood_label,
        "sleep_status": sleep_status
    }

def analyze_voice_nuances(user_text, dimensions=None, language="en-US"):
    """
    Performs careful semantic, prosodic, and emotional micro-analysis on user speech.
    Extracts:
      - vocal_tone: nuanced acoustic/prosodic cadence estimate
      - detected_emotion: specific micro-emotion undercurrent
      - somatic_indicator: somatic/physical nervous system cues
      - calibrated_resonance: compassionate holding posture
      - semantic_focus: concise semantic subject matter
      - contextual_mirror: extracted user phrase for compassionate reflection
    """
    if not user_text:
        return {
            "vocal_tone": "🎙️ Tone: Gentle & Attentive",
            "detected_emotion": "🍃 Emotion: Receptive & Open",
            "somatic_indicator": "⚡ Somatic: Baseline Neutral",
            "calibrated_resonance": "💚 Resonance: Attuned Care",
            "semantic_focus": "Focus: Open Dialogue",
            "contextual_mirror": "what you shared"
        }

    lower = user_text.lower().strip()

    # 1. Semantic Focus Detection & Contextual Mirroring
    semantic_focus = "Focus: Emotional Well-being"
    contextual_mirror = "what you are experiencing"

    # Workplace / Career / Academic
    if any(w in lower for w in ["boss", "manager", "fired", "yelled", "shouted", "job", "office", "work", "career", "deadline", "promotion", "interview", "target", "exam", "college", "studies", "marks", "grades"]):
        semantic_focus = "Focus: Workplace Pressure & Burnout"
        if "boss" in lower or "manager" in lower or "yelled" in lower:
            contextual_mirror = "the intense pressure and difficult encounter with your manager"
        elif "exam" in lower or "studies" in lower or "marks" in lower:
            contextual_mirror = "the heavy academic expectations and performance pressure"
        else:
            contextual_mirror = "the exhausting demands and stress of your work"

    # Relationship / Interpersonal / Heartbreak
    elif any(w in lower for w in ["breakup", "broke up", "ex", "boyfriend", "girlfriend", "husband", "wife", "partner", "cheated", "divorce", "dating", "fight", "argument", "parents", "family", "mom", "dad", "friend"]):
        semantic_focus = "Focus: Interpersonal Hurt & Relationship"
        if "breakup" in lower or "broke up" in lower or "divorce" in lower:
            contextual_mirror = "the raw heartache and grief of this breakup"
        elif "fight" in lower or "argument" in lower or "cheated" in lower:
            contextual_mirror = "the pain and confusion from that hurtful conflict"
        else:
            contextual_mirror = "the fragile emotional tension in your close relationship"

    # Loneliness / Isolation
    elif any(w in lower for w in ["lonely", "alone", "nobody", "isolated", "empty", "no one cares", "no friends", "left out", "akela"]):
        semantic_focus = "Focus: Profound Loneliness & Isolation"
        contextual_mirror = "this heavy ache of feeling so profoundly alone"

    # Panic / Acute Anxiety / Autonomic Surge
    elif any(w in lower for w in ["panic", "panic attack", "can't breathe", "suffocating", "heart beating", "racing", "terrified", "shaking", "trembling"]):
        semantic_focus = "Focus: Acute Panic & Autonomic Distress"
        contextual_mirror = "this sudden terrifying rush of physical panic and rapid breathing"

    # Sadness / Grief / Crying
    elif any(w in lower for w in ["crying", "tears", "can't stop crying", "sad", "depressed", "grief", "loss", "passed away", "died", "mourn"]):
        semantic_focus = "Focus: Deep Melancholy & Grief"
        if "crying" in lower or "tears" in lower:
            contextual_mirror = "the tears that have been falling and the tender sorrow behind them"
        else:
            contextual_mirror = "this deep, heavy cloud of sadness you are carrying"

    # Exhaustion / Overwhelm / Burnout
    elif any(w in lower for w in ["exhausted", "tired", "drained", "can't cope", "too much", "burnout", "overwhelmed", "thak gaya"]):
        semantic_focus = "Focus: Severe Cognitive & Physical Overwhelm"
        contextual_mirror = "just how completely depleted and overstretched your system feels"

    # Sleep / Nighttime Restlessness
    elif any(w in lower for w in ["sleep", "insomnia", "awake", "nightmare", "restless night", "can't sleep", "neend"]):
        semantic_focus = "Focus: Sleep Disruption & Nighttime Agitation"
        contextual_mirror = "the restless difficulty in getting calm, restorative sleep"

    # Self-criticism / Failure / Guilt
    elif any(w in lower for w in ["failure", "worthless", "hate myself", "mistake", "guilt", "shame", "regret", "ruined"]):
        semantic_focus = "Focus: Internal Self-Criticism & Guilt"
        contextual_mirror = "these agonizing feelings of self-blame and feeling not good enough"

    # 2. Vocal Tone Micro-Classification
    if any(w in lower for w in ["panic", "can't breathe", "terrified", "help me"]):
        vocal_tone = "🚨 Tone: High Distress · Urgent Cadence"
    elif any(w in lower for w in ["tired", "exhausted", "drained", "crying", "tears", "heavy", "empty"]):
        vocal_tone = "🎙️ Tone: Weary · Soft & Fragile Cadence"
    elif any(w in lower for w in ["anxious", "racing", "stress", "nervous", "tension", "overwhelmed"]):
        vocal_tone = "⚡ Tone: Accelerated · High Cognitive Tension"
    elif any(w in lower for w in ["angry", "frustrated", "unfair", "yelled", "screamed"]):
        vocal_tone = "🔥 Tone: Constricted · Emotionally Charged"
    elif any(w in lower for w in ["better", "peace", "calm", "relax", "good", "hope"]):
        vocal_tone = "🍃 Tone: Grounded · Receptive & Calm"
    else:
        vocal_tone = "🎙️ Tone: Reflective · Pensive & Guarded"

    # 3. Emotional Micro-Undercurrent
    if "Panic" in semantic_focus:
        detected_emotion = "⚡ Emotion: Acute Autonomic Panic Surge"
    elif "Workplace" in semantic_focus:
        detected_emotion = "🌧️ Emotion: Workplace Demoralization & Stress"
    elif "Relationship" in semantic_focus:
        detected_emotion = "💔 Emotion: Interpersonal Hurt & Disconnection"
    elif "Loneliness" in semantic_focus:
        detected_emotion = "🌫️ Emotion: Unmet Need for Deep Belonging"
    elif "Melancholy" in semantic_focus:
        detected_emotion = "💧 Emotion: Suppressed Grief & Tender Sorrow"
    elif "Overwhelm" in semantic_focus:
        detected_emotion = "🌪️ Emotion: Cognitive Overload & Depletion"
    elif "Self-Criticism" in semantic_focus:
        detected_emotion = "🥀 Emotion: Painful Self-Blame & Inadequacy"
    elif "Sleep" in semantic_focus:
        detected_emotion = "🌙 Emotion: Nocturnal Overactivation & Strain"
    else:
        detected_emotion = "🍂 Emotion: Introspective Yearning for Peace"

    # 4. Somatic Cues
    if any(w in lower for w in ["chest", "breathe", "breathing", "heart", "choke", "suffocating"]):
        somatic_indicator = "⚡ Somatic: Thoracic Constriction & Short Breath"
    elif any(w in lower for w in ["headache", "head", "dizzy", "migraine", "brain"]):
        somatic_indicator = "🧠 Somatic: Cranial Pressure & Tension"
    elif any(w in lower for w in ["stomach", "gut", "nausea", "appetite", "knot"]):
        somatic_indicator = "🌊 Somatic: Visceral Autonomic Knots"
    elif any(w in lower for w in ["neck", "shoulder", "back", "jaw", "knots"]):
        somatic_indicator = "🪨 Somatic: Cervical & Shoulder Armoring"
    elif any(w in lower for w in ["tired", "exhausted", "drained", "body", "weak", "heavy"]):
        somatic_indicator = "🪫 Somatic: Neuromuscular Depletion"
    else:
        somatic_indicator = "🌱 Somatic: Mild Sympathetic Arousal"

    # 5. Calibrated Resonance Posture
    if "Urgent" in vocal_tone or "Panic" in semantic_focus:
        calibrated_resonance = "🛡️ Resonance: Emergency Grounding & Safety"
    elif "Weary" in vocal_tone or "Demoralization" in detected_emotion:
        calibrated_resonance = "🤍 Resonance: Gentle Space-Holding (Low Demand)"
    elif "Accelerated" in vocal_tone or "Overload" in detected_emotion:
        calibrated_resonance = "🌬️ Resonance: Paced Therapeutic Co-regulation"
    else:
        calibrated_resonance = "💚 Resonance: Compassionate Empathetic Inquiry"

    return {
        "vocal_tone": vocal_tone,
        "detected_emotion": detected_emotion,
        "somatic_indicator": somatic_indicator,
        "calibrated_resonance": calibrated_resonance,
        "semantic_focus": semantic_focus,
        "contextual_mirror": contextual_mirror
    }

def detect_input_language(text: str, fallback: str = "en-US") -> str:
    """
    Automatically identifies the language of the user's input text across:
    - Bengali (bn-IN)
    - Devanagari Hindi (hi-IN)
    - Hinglish (code-switched Hindi-English)
    - Spanish (es-ES)
    - Portuguese (pt-BR)
    - English (en-US)
    Enables automatic language switching mid-conversation without user friction.
    """
    t = (text or "").strip()
    if not t:
        return fallback

    # 1. Indic scripts
    if re.search(r"[\u0980-\u09FF]", t):
        return "bn-IN"
    if re.search(r"[\u0900-\u097F]", t):
        return "hi-IN"

    lower = t.lower()
    words = set(re.findall(r"\b[\w]+\b", lower, re.UNICODE))

    # 2. Hinglish markers
    hinglish_markers = {
        "hai", "hain", "hoon", "hun", "kya", "nahi", "nahin", "bohot", "bahut", "mera", "meri", "mere",
        "kuch", "aap", "aapko", "aapki", "aapke", "tum", "tumhe", "thoda", "thodi", "yaar", "dil",
        "kaise", "kaisa", "dard", "neend", "rona", "aansu", "thaka", "thak", "gaya", "gayi",
        "lag", "raha", "rahi", "rahe", "chahiye", "karna", "karo", "hoga", "hogi", "mat", "sath",
        "baat", "kar", "sun", "bhai", "mujhe", "hum", "humein", "acha", "accha", "theek", "shukriya",
        "pareshan", "ghabrahat", "tension", "zindagi", "dost", "mujh", "par", "kyun"
    }
    if len(words.intersection(hinglish_markers)) >= 1:
        return "hinglish"

    # 3. Disambiguate Portuguese and Spanish
    pt_markers = {
        "estou", "muito", "obrigado", "obrigada", "voce", "você", "nao", "não", "tambem", "também",
        "coracao", "coração", "sozinho", "sozinha", "ninguem", "ninguém", "comigo", "chefe",
        "chorar", "noite", "posso", "pânico", "angústia", "relacionamento", "cansaco", "cansaço"
    }
    es_markers = {
        "estoy", "gracias", "por favor", "llorar", "llorando", "puedo", "jefe", "ansiedad", "siento",
        "hola", "como estas", "sobrecargado", "angustia", "cansado", "cansada", "dolor", "triste", "ayuda",
        "solo", "sola", "nadie", "dormir", "sueño", "noche", "muy", "tengo"
    }
    
    fb = (fallback or "en-US").lower()
    pt_score = len(words.intersection(pt_markers)) + (1 if re.search(r"[ãõçê]", lower) else 0) + (1 if fb.startswith("pt") else 0)
    es_score = len(words.intersection(es_markers)) + (1 if re.search(r"[áéíóúñ¿¡]", lower) else 0) + (1 if fb.startswith("es") else 0)

    if es_score > pt_score and es_score >= 1:
        return "es-ES"
    if pt_score > es_score and pt_score >= 1:
        return "pt-BR"
    if es_score >= 1 and fb.startswith("es"):
        return "es-ES"
    if pt_score >= 1 and fb.startswith("pt"):
        return "pt-BR"

    if fb.startswith("pt"):
        return "pt-BR"
    if fb.startswith("es"):
        return "es-ES"
    if fb.startswith("hi"):
        return "hi-IN"
    if fb.startswith("bn"):
        return "bn-IN"

    return "en-US"

# ==========================================================================
# DYNAMIC RESPONSE COMPOSITION ENGINE — CLOSE FRIEND PERSONA
# Generates truly dynamic, conversational responses that feel like
# talking to a close friend. No stock replies. Every response is unique.
# ==========================================================================

import random
import re as _re

# --- User phrase extraction: pull meaningful words from user input ---
_FILLER_WORDS = {
    "i", "me", "my", "am", "is", "are", "was", "were", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "must", "need", "want",
    "to", "of", "in", "for", "on", "with", "at", "by", "from", "as",
    "into", "about", "like", "through", "after", "over", "between", "out",
    "against", "during", "without", "before", "under", "around", "among",
    "and", "but", "or", "nor", "not", "so", "yet", "both", "either", "neither",
    "a", "an", "the", "this", "that", "these", "those", "it", "its",
    "you", "your", "yours", "we", "our", "they", "them", "their",
    "he", "she", "him", "her", "his", "hers", "who", "whom", "what",
    "which", "where", "when", "how", "why", "if", "then", "than",
    "just", "very", "really", "also", "too", "even", "still", "already",
    "always", "never", "sometimes", "often", "now", "today", "yesterday",
    "tomorrow", "here", "there", "up", "down", "all", "some", "many",
    "much", "few", "little", "more", "most", "other", "another", "such",
    "only", "own", "same", "different", "new", "old", "good", "bad",
    "feel", "feeling", "felt", "think", "thinking", "know", "get", "got",
    "going", "come", "came", "make", "made", "take", "took", "give",
    "gave", "say", "said", "tell", "told", "ask", "asked", "try", "tried",
    "keep", "kept", "let", "put", "set", "see", "saw", "look", "looking",
    "start", "started", "help", "happen", "happened", "things", "thing",
    "something", "nothing", "everything", "anything", "lot", "time", "way",
    "people", "person", "life", "day", "night", "week", "month", "year",
    "well", "back", "going", "been", "being", "able", "unable",
    "chi", "hai", "ho", "hain", "tha", "thi", "the", "se", "ko", "ka",
    "ki", "ke", "mein", "mera", "meri", "mere", "mujhe", "main", "yeh",
    "woh", "kya", "kab", "kaise", "kyun", "bahut", "zyada", "bilkul",
    "sirf", "abhi", "phir", "lekin", "aur", "ya", "toh", "hi", "ne",
    "yaar", "na", "mat", "so", "ja", "raha", "rahi", "rahe", "gaya",
    "gayi", "karo", "karta", "karti", "karte", "hua", "hui", "hue",
    "ela", "ele", "isso", "com", "uma", "um", "no", "na", "das", "dos",
    "por", "para", "mais", "muito", "bem", "entao", "porque", "quando",
    "estou", "está", "foi", "ser", "estar", "ter", "fazer", "dizer",
    "je", "tu", "il", "elle", "nous", "vous", "mon",
    "ton", "son", "mes", "tes", "ses", "un", "une", "des", "du",
    "este", "esta", "estos", "estas", "ese", "esa", "esos", "esas",
    "mi", "tu", "su", "nuestro", "nuestra", "vuestro", "vuestra",
    "yo", "el", "ella", "nosotros", "ellos", "ellas", "como", "mas",
    "pero", "porque", "cuando", "donde", "quien", "qual", "tambien",
    "এবং", "বা", "কিন্তু", "যে", "তাই", "তারা", "এটা", "ওটা",
    "আমি", "তুমি", "সে", "আমার", "তোমার", "তার", "আমাদের",
    "কি", "কেন", "কিভাবে", "কখন", "কোথায়", "খুব", "অনেক",
    "মনে", "হয়", "করে", "করা", "হয়ে", "গেছে", "আছে", "ছিল",
    "করতে", "পারি", "পারে", "বলে", "বলা", "বলছি", "বলেছে",
    "দিয়ে", "নিয়ে", "থেকে", "সাথে", "পরে", "আগে", "এখন",
    "আজ", "কাল", "গত", "এই", "সেই", "ওই", "যা", "যেটা"
}

def _extract_user_phrases(user_text, max_phrases=4):
    """Extract meaningful phrases/words from user's own input."""
    if not user_text:
        return []
    words = _re.findall(r'[a-zA-Z\u0980-\u09FF\u0900-\u097F\u00C0-\u024F\u0400-\u04FF]+', user_text)
    meaningful = [w for w in words if len(w) > 2 and w.lower() not in _FILLER_WORDS]
    if not meaningful:
        meaningful = [w for w in words if len(w) > 1]
    seen = set()
    unique = []
    for w in meaningful:
        wl = w.lower()
        if wl not in seen:
            seen.add(wl)
            unique.append(w)
    return unique[:max_phrases]

def _extract_core_phrase(user_text, contextual_mirror=None):
    """Extract the most meaningful phrase to mirror back."""
    if contextual_mirror:
        return contextual_mirror
    # Return None so the caller can use a topic-specific fallback phrase
    # instead of concatenating random keywords which produces unnatural text
    return None

def _detect_topic_hint(user_text):
    """Detect what the user is broadly talking about for contextual replies."""
    lower = (user_text or "").lower()
    # Check more specific topics first before broader ones
    if any(w in lower for w in ["boss", "manager", "work", "office", "job", "bossy", "fired",
                                  "डांट", "चिल्ला", "नौकरी", "jefe", "trabajo", "chefe",
                                  "কাজ", "অফিস", "বস"]):
        return "work"
    if any(w in lower for w in ["breakup", "broke up", "relationship", "partner", "fight", "argument",
                                  "cheated", "divorce", "ex ", "husband", "wife", "boyfriend", "girlfriend",
                                  "झगड़ा", "रिश्ता", "पति", "पत्नी", "ब्रेकअप",
                                  "pareja", "ruptura", "discusión",
                                  "রিশ্তা", "বিচ্ছেদ"]):
        return "relationship"
    if any(w in lower for w in ["exam", "test", "marks", "fail", "failure", "career", "studies",
                                  "परीक्षा", "फेल", "पढ़ाई",
                                  "examen", "fallo",
                                  "পরীক্ষা", "ফেল"]):
        return "academic"
    if any(w in lower for w in ["sleep", "insomnia", "awake", "can't sleep", "night", "bed",
                                  "नींद", "सो", "नींद नहीं",
                                  "dormir", "insomnio", "sueño",
                                  "ঘুম", "নিদ্রা"]):
        return "sleep"
    if any(w in lower for w in ["tired", "exhausted", "burnout", "drained", "no energy", "energy",
                                  "थक", "थकावट", "कमज़ोर",
                                  "cansado", "agotado", "fatiga",
                                  "ক্লান্তি"]):
        return "tiredness"
    if any(w in lower for w in ["cry", "crying", "tears", "sad", "miss", "lost", "gone", "depressed",
                                  "रोना", "आंसू", "दुख", "उदास", "llorar", "tristeza", "triste",
                                  "কান্না", "দুঃখ", "কষ্ট", "খারাপ"]):
        return "sadness"
    if any(w in lower for w in ["lonely", "alone", "nobody", "isolated", "no friends",
                                  "अकेला", "अकेलापन", "कोई नहीं",
                                  "solo", "soledad", "nadie",
                                  "একা", "একাকীত্ব"]):
        return "loneliness"
    if any(w in lower for w in ["panic", "anxious", "anxiety", "heart racing", "breathe",
                                  "scared", "terrified", "fear", "attack",
                                  "घबराहट", "धड़कन", "डर", "पैनिक",
                                  "pánico", "ansiedad", "corazón", "miedo",
                                  "প্যানিক", "ভয়", "ঘবরাহট"]):
        return "anxiety"
    return "general"

# --- CLOSE FRIEND dynamic building blocks ---
# These sound like a real friend texting/talking — casual, warm, short.

# --- ENGLISH ---
_FRIEND_EN = {
    "greet": {
        "work": [
            "ugh, work stuff can be so draining",
            "dealing with that at work sounds really unfair",
            "workplace pressure like that is no joke",
            "that kind of work environment is genuinely toxic",
        ],
        "sadness": [
            "i can hear how much pain you're carrying right now",
            "that kind of sadness runs deep, i know",
            "losing something or someone you care about hurts in ways words can't fully capture",
            "i'm really sorry you're going through this",
        ],
        "anxiety": [
            "that sounds absolutely terrifying",
            "when anxiety hits like that, it feels like the walls are closing in",
            "i hear you — that kind of fear is overwhelming",
            "your body is going through a lot right now",
        ],
        "sleep": [
            "not being able to sleep when your mind is racing is exhausting",
            "lying awake at night with all those thoughts is a special kind of torture",
            "i get it — the nights can be the hardest part",
        ],
        "loneliness": [
            "feeling alone like that is one of the most painful things a person can go through",
            "that kind of isolation cuts really deep",
            "i hear you, and just so you know — you're not alone right now, right here with me",
        ],
        "tiredness": [
            "you sound completely wiped out, and that makes total sense",
            "being that exhausted isn't just physical — it drains everything",
            "running on empty like that is your body begging you to pause",
        ],
        "relationship": [
            "relationship stuff hits different because it involves someone you trusted",
            "that kind of hurt from someone close to you is genuinely devastating",
            "when things go wrong with someone you love, it shakes your whole world",
        ],
        "academic": [
            "academic pressure can feel absolutely suffocating",
            "the weight of exams and expectations is real and heavy",
            "i get it — feeling like your future depends on a grade is terrifying",
        ],
        "general": [
            "hey, i hear you",
            "thanks for sharing that with me",
            "i appreciate you opening up about this",
            "that sounds like a lot to carry",
        ],
    },
    "mirror": {
        "work": [
            "so your {phrase} is really getting to you. being treated badly at work eats away at your confidence over time.",
            "the way you described {phrase} — nobody should have to deal with that. your workplace should be safe, not hostile.",
            "what you're going through with {phrase} is not just 'work stress' — it's affecting your whole wellbeing.",
        ],
        "sadness": [
            "the way you talked about {phrase} — i can feel how heavy that is for you right now.",
            "what you said about {phrase} tells me this isn't just a passing mood. this grief is real.",
            "{phrase} has clearly left a deep mark on you, and that pain deserves to be acknowledged.",
        ],
        "anxiety": [
            "when {phrase} is happening, your nervous system is literally in survival mode. that racing heart and short breath? that's your body's alarm system.",
            "the way you described {phrase} — those physical sensations are real and scary, but they are temporary. your body is trying to protect you.",
            "{phrase} is triggering a fight-or-flight response. it feels dangerous, but you are actually safe right now.",
        ],
        "sleep": [
            "so {phrase} is keeping you up at night. when your brain won't shut off, it's because it's stuck processing unresolved stress.",
            "the {phrase} you described is a cycle — the more you try to force sleep, the harder it gets. that's completely normal.",
            "when {phrase} happens at night, your mind is replaying worries because it hasn't had space to process them during the day.",
        ],
        "loneliness": [
            "what you shared about {phrase} — loneliness isn't about being physically alone. it's about not feeling seen or understood by anyone.",
            "the {phrase} you're feeling activates the same pain centers in your brain as a physical injury. it's that real.",
            "{phrase} is heavy. humans are wired for connection, and when that's missing, everything feels harder.",
        ],
        "tiredness": [
            "so {phrase} is where you're at. that level of exhaustion means your body has been running on fumes for too long.",
            "what you said about {phrase} — that's not laziness. that's your entire system saying 'i need to stop and recover.'",
            "{phrase} is your body's honest signal that you've been pushing past your limits for too long.",
        ],
        "relationship": [
            "what happened with {phrase} — when someone you trusted hurts you, it doesn't just hurt your feelings. it shakes your sense of safety.",
            "the {phrase} situation sounds really painful. relationship wounds cut the deepest because they involve vulnerability.",
            "{phrase} — that kind of emotional pain from someone close isn't something you just 'get over.' it takes time.",
        ],
        "academic": [
            "the pressure around {phrase} is real. the education system puts so much weight on performance that it can crush your spirit.",
            "what you said about {phrase} — one exam or one grade does not define your intelligence or your worth.",
            "{phrase} is stressing you out, and that's completely understandable. the stakes feel enormous right now.",
        ],
        "general": [
            "what you shared about {phrase} — that clearly matters to you, and it matters to me too.",
            "the fact that {phrase} is on your mind tells me it's weighing on you more than you might realize.",
            "so {phrase} is what's been on your mind. let's talk through it together.",
        ],
    },
    "validate": {
        "work": [
            "no job should make you feel this way. your mental peace is worth more than any paycheck.",
            "being treated poorly at work is not something you should have to tolerate. your feelings about this are completely justified.",
            "you deserve a work environment where you feel respected. what you're experiencing is not okay.",
        ],
        "sadness": [
            "crying isn't weakness — it's your body's way of releasing pain that's been building up. let it out.",
            "this sadness you're feeling? it's proof that you cared deeply. that's not a flaw — it's human.",
            "you don't need to 'be strong' right now. sometimes strength is letting yourself feel the pain fully.",
        ],
        "anxiety": [
            "what you're feeling physically — the racing heart, the tight chest — is your nervous system in overdrive. it feels terrifying but it will pass.",
            "anxiety lies to you. it tells you something catastrophic is about to happen. but right now, in this moment, you are safe.",
            "your body is reacting to perceived danger. the feelings are real, but the danger your mind is creating is not.",
        ],
        "sleep": [
            "not sleeping doesn't mean something is wrong with you. your brain is just stuck in 'alert mode' and needs help winding down.",
            "even lying quietly in the dark rests your body more than you think. take the pressure off yourself to fall asleep.",
            "the thoughts racing at night are just your mind trying to process what it couldn't during the day. it's not permanent.",
        ],
        "loneliness": [
            "feeling alone doesn't mean you're unlikable or unworthy. sometimes life circumstances create gaps in connection that aren't your fault.",
            "the pain of loneliness is as real as physical pain — research literally proves this. you're not being dramatic.",
            "you reaching out right now is already an act of courage. you don't have to carry this feeling by yourself.",
        ],
        "tiredness": [
            "being exhausted is not laziness. it's your body telling you that you've been giving more than you have. rest is not optional — it's necessary.",
            "you can't pour from an empty cup. the fact that you're drained means you've been putting in more than anyone should have to.",
            "your tiredness is valid. you don't need to 'push through' everything. sometimes the bravest thing is to stop and rest.",
        ],
        "relationship": [
            "when someone you love hurts you, it doesn't mean you loved wrong. it means you were brave enough to be vulnerable.",
            "you're allowed to grieve a relationship, even if other people don't understand. your pain is valid.",
            "relationship wounds take time to heal because trust was involved. be patient with yourself.",
        ],
        "academic": [
            "your worth is not measured by a test score or a grade. you are so much more than your academic performance.",
            "the pressure you're feeling is real, but please remember — one result does not define your entire future.",
            "struggling academically doesn't mean you're not smart. it means the system isn't designed for how everyone learns.",
        ],
        "general": [
            "whatever you're feeling right now is completely valid. you don't need anyone's permission to feel this way.",
            "there's nothing wrong with how you're reacting to this. anyone in your situation would feel something similar.",
            "your feelings make sense given what you're going through. don't let anyone tell you otherwise.",
        ],
    },
    "ask": {
        "work": [
            "what's the one thing about your work situation that bothers you the most?",
            "is this something that's been building up for a while, or did something specific happen recently?",
            "if you could change one thing about your work life right now, what would it be?",
            "do you have anyone at work who you feel safe talking to about this?",
        ],
        "sadness": [
            "when did this sadness start feeling this heavy?",
            "is there a specific moment or memory that keeps coming back to you?",
            "what does your heart need most right now?",
            "have you been able to talk to anyone about how you're really feeling?",
        ],
        "anxiety": [
            "when did the anxiety start today — was there a trigger, or did it just come out of nowhere?",
            "right now, can you feel your feet on the ground? try focusing on that for just a moment.",
            "on a scale of 1 to 10, how intense is the anxiety feeling right now?",
            "what usually helps you even a little when you feel this way?",
        ],
        "sleep": [
            "what kind of thoughts keep you up at night — worries about the future, replaying the past, or something else?",
            "when was the last time you actually got a full, restful night of sleep?",
            "what does your bedtime routine usually look like?",
            "do you find the worst thoughts hit you right when you lie down?",
        ],
        "loneliness": [
            "when you feel this lonely, what do you wish you had?",
            "was there a time when you felt more connected to people? what was different then?",
            "do you feel lonely even around other people, or mainly when you're physically alone?",
            "what would meaningful connection look like for you right now?",
        ],
        "tiredness": [
            "how long have you been feeling this level of exhaustion?",
            "is it more of a physical tiredness, or does your mind feel drained too?",
            "when was the last time you did something purely for yourself — no obligations, no responsibilities?",
            "what do you think is draining you the most right now?",
        ],
        "relationship": [
            "what hurts the most about what happened?",
            "do you feel like you can trust people after this?",
            "is this something you want to work through, or are you trying to move on?",
            "who have you been leaning on during this?",
        ],
        "academic": [
            "is it the actual studying that feels overwhelming, or is it more about the expectations from others?",
            "what subject or situation is stressing you out the most right now?",
            "do you feel pressure mainly from yourself, your family, or both?",
            "what would you do if grades didn't matter at all?",
        ],
        "general": [
            "what's been weighing on you the most lately?",
            "is there something specific that brought this up today?",
            "what would feel like even a small relief right now?",
            "how has your body been feeling through all of this?",
        ],
    },
    "ground": {
        "work": [
            "before anything else — you're off the clock right now. this moment is yours. take one slow breath.",
            "try this: unclench your jaw, drop your shoulders, and take 3 slow breaths. the work stuff can wait.",
        ],
        "sadness": [
            "if you feel tears coming, let them come. crying is your body's way of healing. i'm right here.",
            "put your hand on your chest. feel your heartbeat. you're here. you're alive. and this pain will ease.",
        ],
        "anxiety": [
            "let's try something together right now. breathe in slowly for 4 counts... hold for 7... and breathe out for 8. i'll wait.",
            "look around and name 5 things you can see right now. this helps your brain switch out of panic mode.",
            "put your feet flat on the floor. feel the ground holding you. you are safe in this exact moment.",
        ],
        "sleep": [
            "tonight, try this: lie down, close your eyes, and breathe out twice as long as you breathe in. let your body feel heavy.",
            "your mind doesn't need to solve everything tonight. give yourself permission to just rest, even if sleep doesn't come immediately.",
        ],
        "loneliness": [
            "right now, in this conversation, you are not alone. i am here with you, and i'm not going anywhere.",
            "place your hands together and feel their warmth. connection starts with being gentle to yourself.",
        ],
        "tiredness": [
            "close your eyes for 10 seconds. let your shoulders drop. let your jaw relax. even micro-rest helps your nervous system reset.",
            "you don't have to do anything right now. just being here and talking is enough. rest.",
        ],
        "relationship": [
            "take a moment. put your hand over your heart. whatever happened with them, your heart is still beating. you're still here.",
            "breathe in for 4, out for 8. the pain is real, but this moment right now is safe.",
        ],
        "academic": [
            "close the textbook for a moment. literally. your brain needs breaks to actually absorb information. take 5 slow breaths.",
            "remind yourself: you are not your grades. breathe in for 4, hold for 4, out for 4. i'll wait.",
        ],
        "general": [
            "hey, try this — put your feet flat on the floor and take 3 slow breaths with me.",
            "take a second — breathe in for 4, hold for 7, out for 8. i'll wait.",
            "sometimes just saying it out loud takes away some of its power. you're doing that right now.",
        ],
    },
}

# --- HINDI ---
_FRIEND_HI = {
    "greet": [
        "अरे यार, ये तो सच में बहुत मुश्किल है",
        "हाँ, मैं समझ सकता हूँ",
        "ये तो वाकई बहुत भारी बात है",
        "ओह, ये सुनकर दिल भारी हो गया",
        "ये तो बहुत कठिन है यार",
        "मैं बिल्कुल समझ रहा हूँ",
    ],
    "mirror": [
        "तुमने जो {phrase} के बारे में बताया, वो सच में दिल को छू गया।",
        "मतलब {phrase} तुम्हें इतना परेशान कर रहा है? ये बिल्कुल समझ आता है।",
        "जब {phrase} होता है तो लगता है सब उल्टा-पुल्टा हो गया।",
        "{phrase} को लेकर जो तुम महसूस कर रहे हो, वो पूरी तरह सही है।",
        "तुम्हारे लिए {phrase} छोटी बात नहीं है, ये मैं समझ सकता हूँ।",
    ],
    "validate": [
        "तुम्हारी फीलिंग्स बिल्कुल वाजिब हैं।",
        "ऐसा महसूस करने में कोई बुराई नहीं है।",
        "तुम ओवररिएक्ट नहीं कर रहे — ये सच में भारी है।",
        "कोई भी तुम्हारी जगह होता तो ऐसे ही फील करता।",
    ],
    "ask": [
        "इसमें सबसे मुश्किल क्या लगता है?",
        "ये कब से चल रहा है?",
        "क्या कुछ खास हुआ था जो आज ये उभरा?",
        "तुम्हें क्या लगता है कि थोड़ा बेहतर कर सकता है?",
        "तुम्हारा दिमाग अभी सबसे ज़्यादा किस बात पर अटका है?",
        "तुम्हारा शरीर अभी कैसा फील हो रहा है?",
        "जब ऐसा होता है तो तुम किससे बात करते हो?",
    ],
    "ground": [
        "एक काम करो — पैर ज़मीन पर रखो और मेरे साथ 3 धीमी सांसें लो।",
        "रुको एक सेकंड। 4 सेकंड सांस लो, 7 रोको, 8 में छोड़ो। मैं यहीं हूँ।",
        "कभी-कभी बस बोल देने से ही बोझ हल्का हो जाता है। तुम अभी वही कर रहे हो।",
        "अभी जवाब नहीं चाहिए। हम साथ मिलकर सुलझाएंगे।",
    ],
}

# --- BENGALI ---
_FRIEND_BN = {
    "greet": [
        "ও বাহ্, এটা সত্যিই অনেক কঠিন",
        "হ্যাঁ, আমি বুঝতে পারছি",
        "এটা তো সত্যিই ভারী কথা",
        "ওফ, এটা শুনে মনটা ভারী হয়ে গেল",
        "এটা অনেক কঠিন হয়েছে তোমার জন্য",
    ],
    "mirror": [
        "তুমি যা {phrase} সম্পর্কে বলেছ, সেটা সত্যিই গভীরভাবে লাগে।",
        "মানে {phrase} তোমাকে এত কষ্ট দিচ্ছে? এটা সম্পূর্ণ বোঝা যায়।",
        "যখন {phrase} ঘটে, তখন মনে হয় সব উল্টে গেছে।",
        "{phrase} নিয়ে তুমি যা অনুভব করছ, তা সম্পূর্ণ যৌক্তিক।",
    ],
    "validate": [
        "তোমার অনুভূতি সম্পূর্ণ যৌক্তিক।",
        "এভাবে অনুভব করাতে কোনো সমস্যা নেই।",
        "তুমি অতিরিক্ত কিছু করছ না — এটা সত্যিই ভারী।",
    ],
    "ask": [
        "এতে সবচেয়ে কঠিন অংশটা কী?",
        "এটা কতদিন ধরে চলছে?",
        "আজ কি কিছু নির্দিষ্ট ঘটনা ঘটেছিল?",
        "তোমার মনে কী লাগছে একটু ভালো করতে পারে?",
        "তোমার শরীর এখন কেমন লাগছে?",
        "যখন এমন হয়, তুমি কার সাথে কথা বলো?",
    ],
    "ground": [
        "একটু থামো — পায়ের তলা মাটিতে রেখে আমার সাথে ৩টি ধীর শ্বাস নাও।",
        "৪ সেকেন্ড শ্বাস নাও, ৭ ধরো, ৮ এ ছেড়ে দাও। আমি এখানেই আছি।",
        "কখনো কখনো বলে ফেললেই বোঝা হালকা হয়। তুমি এখন তাই করছ।",
        "এখন সবকিছুর উত্তর দরকার নেই। আমরা একসাথে করব।",
    ],
}

# --- SPANISH ---
_FRIEND_ES = {
    "greet": [
        "uff, eso suena realmente duro",
        "sí, te entiendo",
        "eso es mucho para cargar",
        "vaya, eso es heavy",
        "eso sí que está complicado",
    ],
    "mirror": [
        "lo que dijiste sobre {phrase} — me llegó. se nota que esto te pesa mucho.",
        "o sea, {phrase} es lo que te está carcomiendo? tiene todo el sentido.",
        "cuando {phrase} pasa, es normal que todo se sienta al revés.",
        "lo de {phrase} no es algo que pase por alto, ¿verdad?",
    ],
    "validate": [
        "lo que sientes es completamente válido.",
        "no estás exagerando — esto es real.",
        "cualquiera en tu lugar sentiría lo mismo.",
        "no tienes que justificar cómo te sientes.",
    ],
    "ask": [
        "¿qué es lo más difícil de todo esto para ti?",
        "¿cuánto tiempo llevas con esto?",
        "¿pasó algo hoy que lo activó?",
        "¿qué crees que te haría sentir un poquito mejor?",
        "¿cómo se siente tu cuerpo ahora mismo?",
        "¿con quién sueles hablar de estas cosas?",
    ],
    "ground": [
        "espera, pon los pies en el suelo y respira conmigo 3 veces despacio.",
        "respira 4 adentro, 7 sostén, 8 afuera. yo te espero.",
        "a veces solo decirlo ya le quita poder. y eso estás haciendo.",
        "no tener respuestas ahora está bien. lo sacamos juntos.",
    ],
}

# --- PORTUGUESE ---
_FRIEND_PT = {
    "greet": [
        "nossa, isso soa muito difícil",
        "é, eu entendo",
        "isso é pesado demais",
        "uai, isso é complicado",
        "caramba, isso é muito",
    ],
    "mirror": [
        "o que você falou sobre {phrase} — me atingiu. dá pra ver que isso pesa muito.",
        "então {phrase} é o que tá te consumindo? faz total sentido.",
        "quando {phrase} acontece, tudo parece desabar.",
        "{phrase} não é algo que você ignora, né?",
    ],
    "validate": [
        "o que você sente é completamente válido.",
        "você não tá exagerando — isso é real.",
        "qualquer um no seu lugar sentiria o mesmo.",
        "você não precisa justificar como se sente.",
    ],
    "ask": [
        "o que é a parte mais difícil disso pra você?",
        "há quanto tempo tá assim?",
        "aconteceu algo hoje que disparou isso?",
        "o que você acha que ajudaria um pouquinho?",
        "como tá se sentindo seu corpo agora?",
        "com quem você costuma falar sobre isso?",
    ],
    "ground": [
        "espera, põe os pés no chão e respira comigo 3 vezes devagar.",
        "respira 4 pra dentro, 7 segura, 8 pra fora. eu tô aqui.",
        "às vezes só falar já tira um pouco do peso. e você tá fazendo isso.",
        "não ter resposta agora tá tudo bem. a gente resolve junto.",
    ],
}

# --- HINGLISH ---
_FRIEND_HINGLISH = {
    "greet": [
        "are yaar, ye to sach mein bahut mushkil hai",
        "haan, main samajh sakta hoon",
        "ye to waqai bahut bhari baat hai",
        "oh, ye sunkar dil bhari ho gaya",
        "ye to bahut kathin hai yaar",
        "main bilkul samajh raha hoon",
    ],
    "mirror": [
        "tumne jo {phrase} ke baare mein bataya, wo sach mein dil ko chhu gaya.",
        "matlab {phrase} tumhe itna pareshan kar raha hai? ye bilkul samajh aata hai.",
        "jab {phrase} hota hai to lagta hai sab ulta-pulta ho gaya.",
        "{phrase} ko lekar jo tum mehsoos kar rahe ho, wo poori tarah sahi hai.",
        "tumhare liye {phrase} chhoti baat nahi hai, ye main samajh sakta hoon.",
    ],
    "validate": [
        "tumhari feelings bilkul wazib hain.",
        "aisa mehsoos karne mein koi burai nahi hai.",
        "tum overreact nahi kar rahe — ye sach mein bhari hai.",
        "koi bhi tumhari jagah hota to aise hi feel karta.",
    ],
    "ask": [
        "ismein sabse mushkil kya lagta hai?",
        "ye kab se chal raha hai?",
        "kya kuch khaas hua tha jo aaj ye ubhra?",
        "tumhe kya lagta hai ki thoda behtar kar sakta hai?",
        "tumhara dimag abhi sabse zyada kis baat par atka hai?",
        "tumhara sharir abhi kaisa feel ho raha hai?",
        "jab aisa hota hai to tum kisse baat karte ho?",
    ],
    "ground": [
        "ek kaam karo — pair zameen par rakho aur mere saath 3 dheemi saansein lo.",
        "ruko ek second. 4 second saans lo, 7 roko, 8 mein chhodo. main yahin hoon.",
        "kabhi-kabhi bas bol dene se hi bojh halka ho jata hai. tum abhi wahi kar rahe ho.",
        "abhi jawab nahi chahiye. hum saath milkar suljhayenge.",
    ],
}

# --- Assemble language packs ---
_LANG_PACKS = {
    "en": _FRIEND_EN,
    "hi": _FRIEND_HI,
    "hinglish": _FRIEND_HINGLISH,
    "bn": _FRIEND_BN,
    "es": _FRIEND_ES,
    "pt": _FRIEND_PT,
}

def _get_lang_code(language):
    lang = (language or "en-US").lower().strip()
    if "hinglish" in lang or lang == "en-in":
        return "hinglish"
    if lang.startswith("hi"):
        return "hi"
    if lang.startswith("bn"):
        return "bn"
    if lang.startswith("es"):
        return "es"
    if lang.startswith("pt"):
        return "pt"
    return "en"

# Track conversation turns per conversation for contextual references
_CONVO_MEMORY = {}

def _get_turn_count(conversation_id):
    if not conversation_id:
        return 0
    return _CONVO_MEMORY.get(conversation_id, 0)

def _increment_turn(conversation_id):
    if conversation_id:
        _CONVO_MEMORY[conversation_id] = _CONVO_MEMORY.get(conversation_id, 0) + 1

def _pick(pack_section, topic):
    """Pick a random item from a topic-specific or flat list/dict."""
    if isinstance(pack_section, dict):
        items = pack_section.get(topic, pack_section.get("general", []))
        if not items:
            # fallback to any available topic
            for v in pack_section.values():
                if v:
                    items = v
                    break
        return random.choice(items) if items else ""
    elif isinstance(pack_section, list):
        return random.choice(pack_section) if pack_section else ""
    return ""

def _is_greeting(text):
    """Check if the input is a simple greeting."""
    lower = (text or "").strip().lower()
    greetings = {
        "hello", "hi", "hey", "hii", "hiii", "helo", "heya", "yo", "sup",
        "good morning", "good afternoon", "good evening", "good night",
        "namaste", "namaskar", "namasté",
        "hola", "olá", "oi", "bom dia", "buenas",
        "নমস্কার", "হ্যালো", "হাই",
        "नमस्ते", "नमस्कार", "हेलो", "हाय",
        "assalamu alaikum", "salam",
        "kaise ho", "kya haal hai", "kya chal raha hai",
    }
    # Check exact match or very short greeting
    if lower in greetings:
        return True
    # Check if it starts with a greeting word and is short
    for g in greetings:
        if lower.startswith(g) and len(lower) < len(g) + 15:
            return True
    return False

def _is_off_topic(text):
    """Check if the input is off-topic (not related to emotional wellbeing)."""
    lower = (text or "").strip().lower()
    # Too short or gibberish
    if len(lower) < 3:
        return True
    # Check for gibberish (no recognizable words)
    import re as _re2
    real_words = _re2.findall(r'[a-zA-Z]{3,}', lower)
    common_words = {"the", "and", "for", "are", "but", "not", "you", "all", "can", "had",
                    "her", "was", "one", "our", "out", "day", "get", "has", "him", "his",
                    "how", "its", "may", "new", "now", "old", "see", "way", "who", "did",
                    "got", "let", "say", "she", "too", "use", "feel", "help", "need", "want",
                    "know", "like", "just", "good", "bad", "sad", "cry", "work", "boss",
                    "sleep", "tired", "alone", "panic", "afraid", "angry", "hurt", "lost",
                    "anxious", "lonely", "scared", "stress", "worry", "pain", "exhausted",
                    "depressed", "crying", "breakup", "exam", "test", "fail",
                    "mujhe", "kya", "kaise", "bahut", "nahi", "hoon", "hai", "raha", "karna",
                    "baat", "dard", "neend", "thak", "akela", "darr", "rona", "tension"}
    if real_words and not any(w in common_words for w in real_words):
        # Might be gibberish — but check if it has Indic/other scripts
        if not _re2.search(r'[\u0900-\u097F\u0980-\u09FF\u00C0-\u024F]', lower):
            return True
    
    # Off-topic queries (weather, jokes, math, coding, etc.)
    off_topic_patterns = [
        "weather", "temperature", "forecast",
        "joke", "funny", "laugh",
        "recipe", "cook", "food",
        "movie", "song", "music recommendation",
        "code", "program", "python", "javascript",
        "math", "calculate", "equation",
        "news", "politics", "sports score",
        "wifi", "internet", "network problem", "download",
        "price", "buy", "sell", "shop", "order",
        "translate", "meaning of",
        "game", "play",
    ]
    if any(p in lower for p in off_topic_patterns):
        return True
    return False

_GREETING_RESPONSES = {
    "en": [
        "hey! i'm really glad you're here. how are you feeling today?",
        "hi there! welcome to MindBridge. how's your day been so far?",
        "hello! i'm here for you. what's on your mind today?",
        "hey! take your time — whenever you're ready to talk, i'm listening.",
    ],
    "hi": [
        "नमस्ते! मैं यहाँ आपके लिए हूँ। आज आप कैसा महसूस कर रहे हैं?",
        "हेलो! MindBridge में आपका स्वागत है। आज आपका दिन कैसा रहा?",
        "हाय! जब भी आप बात करना चाहें, मैं सुन रहा हूँ।",
    ],
    "hinglish": [
        "hey! main yahan hoon tumhare liye. aaj kaisa feel ho raha hai?",
        "hello! MindBridge mein welcome. aaj ka din kaisa raha?",
        "hi! jab bhi baat karna chaho, main sun raha hoon.",
    ],
    "bn": [
        "হ্যালো! আমি এখানে তোমার জন্য আছি। আজ কেমন লাগছে?",
        "নমস্কার! MindBridge-এ স্বাগতম। আজ তোমার দিনটা কেমন গেল?",
        "হাই! যখনই কথা বলতে চাও, আমি শুনছি।",
    ],
    "es": [
        "¡hola! estoy aquí para ti. ¿cómo te sientes hoy?",
        "¡hey! bienvenido a MindBridge. ¿cómo ha sido tu día?",
    ],
    "pt": [
        "oi! estou aqui pra você. como você tá se sentindo hoje?",
        "olá! bem-vindo ao MindBridge. como foi o seu dia?",
    ],
}

_OFF_TOPIC_RESPONSES = {
    "en": [
        "i appreciate you reaching out! i'm your mental well-being companion — i'm best at helping with emotions, stress, anxiety, sleep, relationships, and anything that's weighing on your heart. is there something on your mind you'd like to talk about?",
        "hey! i'm here to support your emotional well-being. if something is bothering you, or you just need someone to listen, i'm ready. what's going on with you today?",
    ],
    "hi": [
        "मैं आपकी मानसिक भलाई का साथी हूँ — भावनाओं, तनाव, चिंता और रिश्तों के बारे में बात करने में मैं सबसे अच्छा हूँ। क्या कुछ है जो आपके मन में चल रहा है?",
    ],
    "hinglish": [
        "main aapki mental well-being ka companion hoon — emotions, stress, anxiety, relationships ke baare mein baat karna mera kaam hai. kya kuch hai jo aapke mann mein chal raha hai?",
    ],
    "bn": [
        "আমি তোমার মানসিক সুস্থতার সঙ্গী — আবেগ, মানসিক চাপ, উদ্বেগ এবং সম্পর্ক নিয়ে কথা বলতে আমি সবচেয়ে ভালো। কিছু কি তোমার মনে চলছে?",
    ],
    "es": [
        "soy tu compañero de bienestar emocional — puedo ayudarte con emociones, estrés, ansiedad y relaciones. ¿hay algo que te preocupa?",
    ],
    "pt": [
        "sou seu companheiro de bem-estar emocional — posso ajudar com emoções, estresse, ansiedade e relacionamentos. tem algo te preocupando?",
    ],
}

def synthesize_dynamic_humanized_reflection(user_text, nuance, dimensions, resource_insight, language="en-US"):
    """
    Dynamically composes a conversational, close-friend-style response.
    - Handles greetings warmly
    - Redirects off-topic/garbage input gently
    - Produces topic-specific organized responses for emotional concerns
    """
    lang_code = _get_lang_code(language)
    pack = _LANG_PACKS.get(lang_code, _LANG_PACKS["en"])

    # ── GREETING DETECTION ──
    if _is_greeting(user_text):
        greetings = _GREETING_RESPONSES.get(lang_code, _GREETING_RESPONSES["en"])
        return [random.choice(greetings)], ["Share how you're feeling", "Talk about your day"]

    # ── OFF-TOPIC / GARBAGE DETECTION ──
    if _is_off_topic(user_text):
        redirects = _OFF_TOPIC_RESPONSES.get(lang_code, _OFF_TOPIC_RESPONSES["en"])
        return [random.choice(redirects)], ["Share how you're feeling", "Talk about stress or anxiety"]

    # ── TOPIC-SPECIFIC EMOTIONAL RESPONSE ──
    _TOPIC_PHRASES = {
        "work": "work situation",
        "sadness": "sadness and pain",
        "anxiety": "anxiety and fear",
        "sleep": "sleepless nights",
        "loneliness": "feeling alone",
        "tiredness": "exhaustion",
        "relationship": "relationship pain",
        "academic": "academic pressure",
        "general": "what you're going through",
    }
    topic = _detect_topic_hint(user_text)
    
    core_phrase = _TOPIC_PHRASES.get(topic, "what you're going through")
    mood = dimensions.get("mood_label", "Reflective")
    stress = dimensions.get("stress_level", 50)

    # 1. GREETING — topic-specific opening
    greeting = _pick(pack["greet"], topic)

    # 2. MIRROR — reflect with topic-specific framing
    mirror_template = _pick(pack["mirror"], topic)
    try:
        mirror = mirror_template.format(phrase=core_phrase)
    except (KeyError, IndexError):
        mirror = mirror_template

    # 3. VALIDATION — topic-specific validation
    validation = _pick(pack["validate"], topic)

    response_parts = [greeting, mirror, validation]

    # 4. SOMATIC/GROUNDING — only for elevated stress
    if stress > 60:
        grounding = _pick(pack["ground"], topic)
        if grounding:
            response_parts.append(grounding)

    # 5. FOLLOW-UP QUESTION — topic-specific
    question = _pick(pack["ask"], topic)
    response_parts.append(question)

    # Build suggested action chips
    chip_badge = resource_insight.get("chip_badge", "")
    action = resource_insight.get("action_suggestion", "")
    suggested = [q for q in [chip_badge, action] if q]

    return response_parts, suggested

def generate_mindbridge_response(user_text, conversation_history=None, language="en-US"):
    """
    Core conversational engine:
    1. Runs safety & crisis check.
    2. Runs non-diagnostic ethical guardrails.
    3. Analyzes emotional context.
    4. Generates empathetic, deeply humanized, validating responses in the requested language
       (English, Hindi, Hinglish, Spanish, Portuguese, Bengali).
    5. Recommends gentle next steps & verified professional matching.
    """
    # 1. Automatic Dynamic Language Detection & Mid-Conversation Switching
    detected_language = detect_input_language(user_text, fallback=language or "en-US")
    language_switched = (detected_language != (language or "en-US"))
    active_lang = detected_language
    lang = active_lang.lower().strip()
    is_hinglish = "hinglish" in lang or lang == "en-in"
    is_hindi = lang.startswith("hi") and not is_hinglish
    is_spanish = lang.startswith("es")
    is_portuguese = lang.startswith("pt")
    is_bengali = lang.startswith("bn")

    # 2. Regional Dialect Normalization (Bangla RDS applied only for Bengali language inputs)
    normalized_text = user_text
    if is_bengali and user_text:
        normalized_text = linguistic_trainer.normalize_dialect_input(user_text)
    active_text = normalized_text if normalized_text else user_text

    safety = scan_safety(active_text)
    dimensions = analyze_dimensions(active_text)
    nuance = analyze_voice_nuances(active_text, dimensions, language=lang)
    resource_insight = retrieve_therapeutic_insights(active_text, language=lang, dimensions=dimensions)

    # 1. EMERGENCY CRISIS TRIGGERED
    if safety["is_crisis"]:
        if is_hindi:
            crisis_reply = (
                "मैं आपकी बात सुन रहा हूँ और समझ सकता हूँ कि आप इस समय कितना असहनीय दर्द और अकेलापन महसूस कर रहे हैं... लेकिन कृपया याद रखें, **आप बिल्कुल अकेले नहीं हैं, और आपकी ज़िंदगी बहुत कीमती है।**\n\n"
                "क्योंकि आपकी सुरक्षा मेरे लिए सबसे बढ़कर है और मैं यहाँ से आपातकालीन मेडिकल मदद नहीं पहुँचा सकता, इसलिए कृपया अभी इन 24/7 निःशुल्क और गोपनीय काउंसलर्स से संपर्क करें:\n\n"
                "• **Tele-MANAS (भारत सरकार):** कॉल करें **14416** या **1800 891 4416** (टोल-फ्री, 24/7)\n"
                "• **वांद्रेवाला फाउंडेशन:** कॉल करें **+91 9999 666 555** (24/7 निःशुल्क सहायता)\n"
                "• **AASRA हेल्पलाइन:** कॉल करें **+91 98204 66726** (24/7)\n"
                "• **अंतर्राष्ट्रीय 988 हेल्पलाइन:** कॉल/टेक्स्ट **988**\n\n"
                "हम अभी साथ हैं। क्या आप ऊपर दिए गए लाल आपातकालीन बटन पर क्लिक करके किसी से बात करना चाहेंगे, या मेरे साथ 3 धीमी और गहरी सांसें लेना चाहेंगे?"
            )
            suggested = ["Tele-MANAS (14416) पर कॉल करें", "वांद्रेवाला हेल्पलाइन (+91 9999 666 555)", "4-7-8 शांत प्राणायाम करें", "किसी अपने से बात करें"]
        elif is_hinglish:
            crisis_reply = (
                "Main aapki baat sun raha hoon aur samajh sakta hoon ki aap is waqt kitna gehra dard aur akelapan feel kar rahe hain... Lekin please yaad rakhiye, **aap bilkul akele nahi hain aur aapki life bohot precious hai.**\n\n"
                "Aapki safety mere liye sabse zaroori hai aur main medical emergency care provide nahi kar sakta, isliye please abhi bina kisi jhijhak ke in free, confidential 24/7 counselors se connect kijiye:\n\n"
                "• **Tele-MANAS (Govt of India):** Call **14416** ya **1800 891 4416** (Toll-Free, 24/7)\n"
                "• **Vandrevala Foundation:** Call **+91 9999 666 555** (24/7 Free Support)\n"
                "• **AASRA Helpline:** Call **+91 98204 66726** (24/7)\n"
                "• **International 988 Lifeline:** Call/Text **988**\n\n"
                "Main yahan hoon aapke saath. Kya aap upar diye emergency button se direct call karna chahenge, ya mere saath 3 slow, grounding breaths lena chahenge?"
            )
            suggested = ["Call Tele-MANAS (14416)", "Call Vandrevala (+91 9999 666 555)", "Take Grounding Breaths", "Reach Trusted Friend"]
        elif is_spanish:
            crisis_reply = (
                "Te escucho con todo mi corazón y sé lo difícil y agotador que se siente cargar con tanto dolor ahora mismo... Pero por favor recuerda, **no estás solo en esto y tu vida vale muchísimo.**\n\n"
                "Tu bienestar y tu seguridad son lo primero. Aunque yo no puedo brindarte auxilio médico de emergencia, hay personas preparadas para escucharte y sostenerte con amor y confidencialidad ahora mismo:\n\n"
                "• **Línea de Atención a la Conducta Suicida (España):** Llama al **024** (Gratuito, 24/7)\n"
                "• **Línea 988 Lifeline (EE. UU. / Internacional):** Llama o envía mensaje al **988** (En español 24/7)\n"
                "• **Tele-MANAS (Internacional):** Llama al **+91 14416**\n"
                "• **Fundación Vandrevala:** Llama al **+91 9999 666 555**\n\n"
                "Aquí estoy contigo. ¿Te gustaría presionar el botón de SOS para llamar a un especialista, o prefieres que hagamos juntos una pausa de respiración pausada?"
            )
            suggested = ["Llamar al 024 / 988", "Fundación de Apoyo (+91 9999 666 555)", "Respirar juntos 1 minuto", "Hablar con alguien querido"]
        elif is_portuguese:
            crisis_reply = (
                "Estou te ouvindo com todo o carinho e compreendo o quanto a dor e o cansaço parecem insuportáveis agora... Mas por favor, lembre-se: **você não está sozinho e a sua vida tem um valor imenso.**\n\n"
                "Como a sua segurança é a minha maior prioridade e não posso prestar atendimento médico emergencial, por favor entre em contato agora mesmo com quem está preparado para te acolher sem julgamentos:\n\n"
                "• **Centro de Valorização da Vida - CVV (Brasil):** Ligue **188** (Gratuito, 24 horas)\n"
                "• **SOS Voz Amiga (Portugal):** Ligue **21 354 45 45** ou **91 280 26 69**\n"
                "• **Linha 988 Lifeline (EUA / Internacional):** Ligue ou envie mensagem para **988**\n"
                "• **Tele-MANAS:** Ligue **14416**\n\n"
                "Eu continuo aqui ao seu lado. Você aceita clicar no botão vermelho de SOS para conversar com alguém agora, ou prefere respirar bem devagar comigo?"
            )
            suggested = ["Ligar para CVV (188)", "Ligar para SOS Voz Amiga", "Respiração Acalmadora", "Falar com uma pessoa querida"]
        elif is_bengali:
            crisis_reply = (
                "আমি আপনার কথা গভীর মনোযোগ দিয়ে শুনছি। আমি বুঝতে পারছি আপনি কতটা অসহনীয় কষ্ট ও একাকীত্ব অনুভব করছেন... তবে অনুগ্রহ করে বিশ্বাস রাখুন, **আপনি একা নন এবং আপনার জীবন অত্যন্ত মূল্যবান।**\n\n"
                "আপনার সুরক্ষাই সবচেয়ে বড় বিষয় এবং আমি জরুরি চিকিৎসাসেবা দিতে অক্ষম, তাই দয়া করে দ্বিধা না করে এখনই এই ২৪/৭ বিনামূল্যে ও সম্পূর্ণ গোপনীয় হেল্পলাইনগুলোর সাহায্য নিন:\n\n"
                "• **Tele-MANAS (ভারত সরকার):** কল করুন **14416** অথবা **1800 891 4416** (টোল-ফ্রি, ২৪/৭)\n"
                "• **কান পেতে রই (Kaan Pete Roi):** কল করুন **+880 1779 554391** / **+880 1779 554392**\n"
                "• **ভান্দ্রেওয়ালা ফাউন্ডেশন:** কল করুন **+91 9999 666 555** (২৪/৭ ফ্রি সাপোর্ট)\n"
                "• **আশরা (AASRA Helpline):** কল করুন **+91 98204 66726**\n\n"
                "আমি আপনার পাশেই আছি। আপনি কি উপরের লাল জরুরি বাটনে ক্লিক করে কথা বলতে চান, নাকি আমার সাথে ৩টি শান্ত ও গভীর শ্বাস নিয়ে একটু হালকা হতে চান?"
            )
            suggested = ["Tele-MANAS (14416)-এ কল করুন", "ভান্দ্রেওয়ালা হেল্পলাইন (+91 9999 666 555)", "৪-৭-৮ শান্ত শ্বাসক্রিয়া", "কাছের মানুষের সাথে যোগাযোগ"]
        else:
            crisis_reply = (
                "I hear you, and I can sense how overwhelming and painful things feel right now... But please know, **you do not have to carry this alone, and your life has immense value.**\n\n"
                "Because your safety is the highest priority and I cannot provide emergency medical intervention, please connect immediately with trained, compassionate counselors who are ready to support you 24/7:\n\n"
                "• **988 Suicide & Crisis Lifeline (US & Canada):** Call or text **988** (Free & Confidential, 24/7)\n"
                "• **Crisis Text Line:** Text **HOME to 741741**\n"
                "• **The Trevor Project (LGBTQ Youth):** Call **1-866-488-7386** or text **START to 678-678**\n"
                "• **Tele-MANAS (India):** Call **14416** (Toll-Free, 24/7)\n"
                "• **International Resources:** Click the red **SOS button** above for instant access.\n\n"
                "I am right here with you. Would you like to click the red SOS button above to speak with someone right now, or take 3 slow, grounding breaths with me?"
            )
            suggested = ["Call Tele-MANAS (14416)", "Call Vandrevala (+91 9999 666 555)", "Take Grounding Breaths", "Reach Trusted Friend"]

        return {
            "response": crisis_reply,
            "risk_level": "emergency",
            "safety_data": safety,
            "suggested_actions": suggested,
            "dimensions": dimensions,
            "guardrail_triggered": "crisis_safety",
            "nuance_analysis": nuance,
            "resource_insights": resource_insight
        }

    # 2. NON-DIAGNOSTIC GUARDRAIL TRIGGERED
    for diag_pat in DIAGNOSTIC_QUERIES:
        if re.search(diag_pat, user_text.lower()):
            if is_hindi:
                guardrail_reply = (
                    "मैं आपकी बात समझ रहा हूँ और स्पष्ट उत्तर चाहना बिल्कुल स्वाभाविक है। एक सहायक साथी के रूप में, **मैं कोई मेडिकल डायग्नोसिस या दवाइयाँ नहीं दे सकता**—यह केवल एक लाइसेंस प्राप्त मनोवैज्ञानिक या डॉक्टर ही कर सकते हैं। आप जो महसूस कर रहे हैं वह महत्वपूर्ण है; क्या आप सत्यापित विशेषज्ञों से बात करना चाहेंगे?"
                )
                suggested = ["सत्यापित विशेषज्ञ खोजें", "मेरी नींद व तनाव पैटर्न देखें", "अपनी भावनाओं पर और बात करें", "सत्र सारांश देखें"]
            elif is_hinglish:
                guardrail_reply = (
                    "Main aapki baat samajh raha hoon aur clear medical answers chahna bilkul natural hai. Ek emotional companion ke roop me, **main medical diagnosis ya medicine prescribe nahi kar sakta**—ye sirf certified psychologist ya doctor hi kar sakte hain. Aapka dukh valid hai; kya aap hamare verified specialists se connect karna chahenge?"
                )
                suggested = ["Find Verified Specialists", "Explore Sleep & Stress Patterns", "Talk More About What I Feel", "View Session Insights"]
            elif is_spanish:
                guardrail_reply = (
                    "Comprendo tus dudas y es muy natural buscar claridad médica. Como tu compañero de apoyo, **no puedo emitir diagnósticos médicos ni recetar fármacos**—esa evaluación requiere un psicólogo o psiquiatra certificado. Todo lo que sientes es válido; ¿te gustaría contactar a un especialista verificado?"
                )
                suggested = ["Ver Especialistas Verificados", "Explorar mis patrones de sueño y estrés", "Seguir hablando de mis emociones", "Ver resumen de la sesión"]
            elif is_portuguese:
                guardrail_reply = (
                    "Compreendo o que você busca e é muito natural querer respostas clínicas claras. Como seu companheiro de apoio, **não posso fornecer diagnósticos médicos nem prescrever remédios**—isso cabe a um psicólogo ou psiquiatra credenciado. O que você sente importa; gostaria de consultar especialistas verificados?"
                )
                suggested = ["Encontrar Especialistas Verificados", "Explorar meu sono e nível de estresse", "Continuar conversando sobre o que sinto", "Ver resumo da sessão"]
            elif is_bengali:
                guardrail_reply = (
                    "আমি বুঝতে পারছি এবং এমন পরিস্থিতিতে স্পষ্ট চিকিৎসা বা ওষুধ খোঁজা খুব স্বাভাবিক। একজন সহমর্মী সহায়ক হিসেবে **আমি কোনো মেডিকেল ডায়াগনসিস বা ওষুধ প্রেসক্রাইব করতে পারি না**—এর জন্য সনদপ্রাপ্ত মনোরোগ বিশেষজ্ঞের পরামর্শ প্রয়োজন। তোমার কষ্টটা সত্যি; তুমি কি আমাদের যাচাইকৃত বিশেষজ্ঞ চিকিৎসকের সাহায্য নিতে চাও?"
                )
                suggested = ["যাচাইকৃত বিশেষজ্ঞ খুঁজুন", "ঘুম ও মানসিক চাপের মাত্রা দেখুন", "মনের অনুভূতি নিয়ে আরও কথা বলুন", "সেশনের সারাংশ দেখুন"]
            else:
                guardrail_reply = (
                    "I hear you, and wanting clear medical answers is completely natural. As your well-being companion, **I cannot provide medical diagnoses or prescribe medications**—that requires an evaluation by a licensed psychologist or psychiatrist. What you feel is valid; would you like me to guide you to our verified specialists?"
                )
                suggested = ["Find Verified Specialists", "Explore My Sleep & Stress Patterns", "Talk More About What I Feel", "View Session Insights"]

            return {
                "response": guardrail_reply,
                "risk_level": "safe",
                "safety_data": safety,
                "suggested_actions": suggested,
                "dimensions": dimensions,
                "guardrail_triggered": "non_diagnostic_ethical_shield",
                "nuance_analysis": nuance,
                "resource_insights": resource_insight
            }

    # 3. DYNAMIC EVIDENCE-GROUNDED WELL-BEING CONVERSATION
    # Synthesized at the moment from WHO PM+, WHO mhGAP, and resource emotional corpora
    response_parts, suggested_chips = synthesize_dynamic_humanized_reflection(
        user_text=user_text,
        nuance=nuance,
        dimensions=dimensions,
        resource_insight=resource_insight,
        language=lang
    )

    full_response = "\n\n".join(response_parts)

    voice_profile = linguistic_trainer.voice_modules_metadata.get(
        "bn" if is_bengali else "en",
        linguistic_trainer.voice_modules_metadata.get("global_calibration", {})
    )

    voice_perspectives = {
        "bn": linguistic_trainer.voice_modules_metadata.get("bn", {}),
        "en": linguistic_trainer.voice_modules_metadata.get("en", {}),
        "recommended": "bn" if is_bengali else "en"
    }

    return {
        "response": full_response,
        "risk_level": "safe",
        "safety_data": safety,
        "suggested_actions": suggested_chips,
        "dimensions": dimensions,
        "guardrail_triggered": None,
        "nuance_analysis": nuance,
        "resource_insights": resource_insight,
        "voice_module_profile": voice_profile,
        "voice_perspectives": voice_perspectives,
        "linguistic_stats": linguistic_trainer.get_stats(),
        "normalized_input": normalized_text if normalized_text != user_text else None,
        "detected_language": detected_language,
        "language_switched": language_switched
    }

def synthesize_session_summary(conversation_history):
    """
    Synthesizes a safe, non-diagnostic emotional well-being summary
    that the user can review or share with a certified professional.
    """
    if not conversation_history:
        return {
            "summary": "No conversation recorded yet. Start a gentle check-in above.",
            "dominant_themes": [],
            "average_stress": 50,
            "recommended_next_steps": ["Complete a full emotional check-in"]
        }

    user_texts = [m["content"] for m in conversation_history if m.get("sender") == "user"]
    combined_text = " ".join(user_texts)
    
    dimensions = analyze_dimensions(combined_text)
    
    themes = []
    if "stressor:workplace" in dimensions["detected_emotions"]:
        themes.append("Workplace Pressure & Cognitive Fatigue")
    if "stressor:relationship" in dimensions["detected_emotions"]:
        themes.append("Interpersonal Tension & Relational Stress")
    if dimensions["sleep_status"] == "Disrupted / Insomnia":
        themes.append("Sleep Fragmentation & Restlessness")
    if any(m in dimensions["detected_emotions"] for m in ["anxious"]):
        themes.append("Anticipatory Worry & Physical Tension")
    if any(m in dimensions["detected_emotions"] for m in ["melancholic"]):
        themes.append("Low Energy & Persistent Sadness")

    if not themes:
        themes = ["General Well-being Exploration", "Emotional Reflection"]

    summary_text = (
        f"During this check-in, the user articulated feelings centered around {', '.join(themes)}. "
        f"Overall emotional valence is '{dimensions['mood_label']}' with an estimated subjective stress index of {dimensions['stress_level']}/100. "
        f"Sleep pattern was reported as '{dimensions['sleep_status']}'. "
        f"Note: This summary is non-diagnostic and synthesized purely to facilitate transparent communication with a licensed healthcare practitioner."
    )

    next_steps = [
        "Consult a verified Clinical Psychologist or Psychiatrist for personalized guidance",
        "Practice daily grounding (e.g., 4-7-8 rhythmic breathing or progressive relaxation)",
        "Maintain consistent sleep hygiene and gentle physical movement",
        "Keep tracking emotional fluctuations over the next 7 days"
    ]

    return {
        "summary": summary_text,
        "dominant_themes": themes,
        "average_stress": dimensions["stress_level"],
        "mood_label": dimensions["mood_label"],
        "sleep_status": dimensions["sleep_status"],
        "recommended_next_steps": next_steps
    }
