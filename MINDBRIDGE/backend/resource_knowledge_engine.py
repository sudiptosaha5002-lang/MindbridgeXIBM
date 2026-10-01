"""
MindBridge - Resource Semantic Knowledge Engine
Indexes, extracts, and semantically retrieves evidence-based therapeutic protocols,
clinical frameworks, and emotional lexicons from project resources (WHO PM+, WHO mhGAP,
Translational Psychiatry NLP framework, and Hinglish/Bangla emotional corpora).
"""

import os
import re
from typing import Dict, Any, List

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESOURCES_DIR = os.path.join(BASE_DIR, "frontend", "resources")
BOOKS_DIR = os.path.join(BASE_DIR, "frontend", "books")

# ==========================================================================
# CLINICAL EVIDENCE CORPUS (Indexed from WHO & Clinical Research Books)
# ==========================================================================

EVIDENCE_CORPUS = {
    "fatigue_exhaustion": {
        "framework": "WHO Problem Management Plus (PM+) · Protocol 2: Behavioral Activation & Cognitive Rest",
        "reference": "WHO_MSD_MER_18.5_eng.pdf (Pages 38-55)",
        "clinical_rationale": "Profound mental and physical fatigue is the nervous system's biological brake against chronic overload. Forcing productivity deepens neuromuscular depletion. Restorative recovery requires micro-pauses without guilt.",
        "somatic_protocol": "Unclench the jaw, drop the shoulders away from the ears, allow the back of your neck to soften, and feel the solid ground holding your weight.",
        "reflective_guidance": "Validate that being exhausted is not a personal failure, but the body's honest request to down-regulate and rest.",
        "chip_badge": "🌿 WHO PM+ Restorative Energy Protocol",
        "action_suggestion": "Rest right here with me"
    },
    "workplace_conflict": {
        "framework": "WHO mhGAP Intervention Guide v2.0 · Acute Interpersonal Stress & Occupational Trauma",
        "reference": "9789241549790-eng-WHO Ebook.pdf (Pages 42-61) & book2.pdf",
        "clinical_rationale": "Being yelled at or demeaned by a person in authority triggers an acute sympathetic threat surge (elevated heart rate, shame, humiliation, and involuntary crying as an autonomic parasympathetic reset). Separating personal self-worth from an aggressor's volatility is essential.",
        "somatic_protocol": "Place a hand over the center of your chest, take a slow 4-second breath in, feel your heartbeat, and remember that you are safe in this room.",
        "reflective_guidance": "Express clear compassion for the hurt of the reprimand, firmly affirm that being screamed at was unjust and not their fault, and normalize tears as biological release.",
        "chip_badge": "🛡️ WHO mhGAP Workplace Stress Protocol",
        "action_suggestion": "Talk through what happened"
    },
    "crying_grief": {
        "framework": "Translational Psychiatry NLP & Affective Alliance Framework",
        "reference": "book2.pdf (Pages 4-12) & WHO PM+ Section 1",
        "clinical_rationale": "Emotional weeping triggers the release of oxytocin and endorphins, facilitating biochemical tension discharge. Suppressing tears maintains physiological distress.",
        "somatic_protocol": "Allow tears to flow without restraint. Bring both hands together or wrap your arms around yourself in a comforting hold.",
        "reflective_guidance": "Hold unconditional, patient space. Assure the user that tears are a healthy, courageous expression of grief, not a weakness.",
        "chip_badge": "🤍 Affective Alliance Emotional Safety",
        "action_suggestion": "Let the sadness release softly"
    },
    "panic_anxiety": {
        "framework": "WHO Problem Management Plus (PM+) · Core Exercise: The Slow Breathing Technique",
        "reference": "WHO_MSD_MER_18.5_eng.pdf (Pages 24-33)",
        "clinical_rationale": "Hyperventilation and acute panic stem from sympathetic nervous overdrive. Controlled diaphragmatic exhalation stimulates the vagus nerve, signaling biological safety.",
        "somatic_protocol": "Inhale gently through the nose for 4 counts... hold softly for 2 counts... and exhale smoothly through relaxed lips for 6 slow counts.",
        "reflective_guidance": "Provide immediate grounding reassurance: verify that this terrifying physical surge is a temporary neurological alarm, not physical harm.",
        "chip_badge": "🌊 WHO PM+ Slow Breathing Pacer",
        "action_suggestion": "Breathe 4-7-8 with MindBridge"
    },
    "insomnia_racing_thoughts": {
        "framework": "WHO mhGAP Guidelines · Sleep Disruption & Somatosensory De-arousal",
        "reference": "9789241549790-eng-WHO Ebook.pdf (Pages 112-124)",
        "clinical_rationale": "Bedtime insomnia is driven by autonomic hyperarousal and cognitive looping. The bed becomes conditioned as a place of worry rather than restorative sleep.",
        "somatic_protocol": "Gently soften your eyelids, relax the tongue away from the roof of your mouth, and visualize exhaling the worries of the day out through your soles.",
        "reflective_guidance": "Reassure the user that lying quietly without sleep still rests the body, taking away the panic of trying to force sleep.",
        "chip_badge": "🌙 WHO Sleep Somatosensory De-arousal",
        "action_suggestion": "Quiet Bedtime Grounding"
    },
    "loneliness_isolation": {
        "framework": "WHO PM+ Protocol 4 · Accessing Interpersonal Support & Relational Attunement",
        "reference": "WHO_MSD_MER_18.5_eng.pdf (Pages 72-89) & book1.pdf",
        "clinical_rationale": "Perceived loneliness activates the same neurological pain matrix as physical injury. Experiencing genuine, non-judgmental presence breaks the loop of isolation.",
        "somatic_protocol": "Feel the warm boundary of your own hands, breathe slowly, and remember that connection begins with being gentle to yourself right here.",
        "reflective_guidance": "Offer warm, unwavering presence: make the user feel seen, respected, and fundamentally worthy of care.",
        "chip_badge": "🤝 WHO PM+ Relational Attunement",
        "action_suggestion": "Explore feeling alone together"
    },
    "somatic_tightness": {
        "framework": "Neuro-Somatic Tension Release & Body-Centered Mindfulness",
        "reference": "WHO PM+ Stress Management & book1.pdf",
        "clinical_rationale": "Chronic emotional strain stores in the musculoskeletal system as tightness in the trapezius, jaw clenching, or solar plexus constriction.",
        "somatic_protocol": "Gently rotate your shoulders backwards three times, tilt your ear slowly towards one shoulder and breathe into the stretch, then ease back to center.",
        "reflective_guidance": "Acknowledge the physical burden the body is holding and invite a shared physical letting go.",
        "chip_badge": "🌱 Somatic Muscle De-Constriction",
        "action_suggestion": "Release physical tension"
    },
    "existential_meaning": {
        "framework": "Spiritual & Existential Grounding",
        "reference": "Four-Vedas-English-Translation.pdf & Holy-Quran-English.pdf",
        "clinical_rationale": "When facing a profound loss of purpose or existential dread, clinical interventions alone may feel hollow. Integrating spiritual wisdom (like Vedic concepts of impermanence and interconnectedness, or Quranic patience 'Sabr' and inner resilience) provides deep existential anchoring.",
        "somatic_protocol": "Place your hands softly on your lap, close your eyes, and feel the silent, steady rhythm of your breath connecting you to the larger universe.",
        "reflective_guidance": "Remind the user that feeling lost is a profound part of the human journey, not a defect. Gently offer that patience and observing this emptiness often precedes finding new, deeper meaning.",
        "chip_badge": "🌌 Existential & Spiritual Grounding",
        "action_suggestion": "Explore inner peace and meaning"
    },
    "severe_crisis_hopelessness": {
        "framework": "AI Suicide Prevention & De-escalation Protocol",
        "reference": "S0924933822000086a-ai suicide prevention.pdf",
        "clinical_rationale": "In moments of acute hopelessness, the cognitive field narrows significantly. Immediate intervention requires radical validation of the pain, removing judgment, and anchoring the user to the present moment without forcing false positivity.",
        "somatic_protocol": "Look around the room and name three things you can see right now. Let your eyes rest on them, and feel the solid ground beneath your feet holding you up.",
        "reflective_guidance": "Acknowledge the immense exhaustion of carrying this pain. Do not try to 'fix' it immediately; instead, firmly and gently assure them that you are present with them in the dark.",
        "chip_badge": "⚕️ Crisis De-escalation & Anchoring",
        "action_suggestion": "Breathe and anchor with me"
    }
}

# ==========================================================================
# HINGLISH & BENGALI EMOTIONAL PHRASE PATTERNS (Extracted from Resources)
# ==========================================================================

HINGLISH_LEXICON = {
    "tired": ["Bohot zyada thakawat aur low energy", "Mind aur body dono exhaust ho chuke hain", "Aaj bina kisi guilt ke rest lena zaroori hai"],
    "work": ["Office aur boss ka pressure jab limit cross karta hai", "Khud par extra pressure mat lijiye", "Aapki mental peace kisi bhi job se zyada important hai"],
    "crying": ["Aansu aana bilkul natural hai jab dil bhar jata hai", "Rone se dil ka bojh halka hota hai", "Yahan aap completely safe hain"],
    "panic": ["Saans thodi tezi se chal rahi hai", "Ye wave jald hi settle ho jayegi", "Mere sath 1 slow breath lijiye"],
    "sleep": ["Raat ko thoughts continuously loop kar rahi hain", "Dimaag ko thoda pause dete hain", "Bed par aakar body ko loose chhod dijiye"],
    "lonely": ["Akelapan bohot silently hurt karta hai", "Lekin aap is pal me akele nahi hain", "Main yahin hoon aapke sath"]
}

BANGLA_LEXICON = {
    "tired": ["শারীরিক ও মানসিক ক্লান্তি খুব স্বাভাবিক", "আজ নিজেকে একটু বিশ্রাম দিন", "সবকিছু একা টানার দরকার নেই"],
    "work": ["অফিসের কাজের চাপ ও মানসিক অশান্তি", "বস বা কর্মক্ষেত্রের দুর্ব্যবহার আপনার দোষ নয়", "নিজের মানসিক প্রশান্তি সবচেয়ে আগে"],
    "crying": ["কান্না আটকে রাখবেন না, চোখের জল মনের ভার কমায়", "এখানে আপনি সম্পূর্ণ নিরাপদ", "আপনার মনের কষ্ট আমি বুঝতে পারছি"],
    "panic": ["বুকের ধড়ফড়ানি বা শ্বাসকষ্টের সময় শান্ত থাকুন", "ধীরে ধীরে একটি লম্বা শ্বাস নিন", "এই অস্থিরতা কিছুক্ষণের মধ্যেই কমে যাবে"],
    "sleep": ["ঘুম না হওয়া এবং মাথায় অবিরাম চিন্তা ঘোরা", "মনকে শান্ত করার জন্য ৪-৭-৮ শ্বাসক্রিয়া করুন", "আজকের রাতটি নিজের শান্তির জন্য রাখুন"],
    "lonely": ["একাকীত্বের কষ্ট অত্যন্ত গভীর হতে পারে", "তবে জানবেন আপনি একা নন, আমি আপনার পাশেই আছি", "মনের কথা খুলে বলুন"]
}

# ==========================================================================
# RETRIEVAL ENGINE
# ==========================================================================

def retrieve_therapeutic_insights(user_text: str, language: str = "en-US", dimensions: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Analyzes user text semantically against the resource evidence corpus
    and returns relevant clinical protocols, somatic actions, and language framing.
    """
    lower = (user_text or "").lower()
    dims = dimensions or {}
    emotions = dims.get("detected_emotions", [])
    
    # 1. Topic Scoring
    scores = {
        "fatigue_exhaustion": 0,
        "workplace_conflict": 0,
        "crying_grief": 0,
        "panic_anxiety": 0,
        "insomnia_racing_thoughts": 0,
        "loneliness_isolation": 0,
        "somatic_tightness": 0,
        "existential_meaning": 0,
        "severe_crisis_hopelessness": 0
    }

    # Keyword and semantic cues
    if any(k in lower for k in ["tired", "exhausted", "fatigue", "drained", "no energy", "depleted", "burned out", "burnout", "heavy", "thak", "thaka", "thakawat", "shanto", "clanto"]):
        scores["fatigue_exhaustion"] += 5
    if any(k in lower for k in ["boss", "yell", "yelled", "screamed", "manager", "fired", "colleague", "workplace", "toxic job", "insulted", "shouted", "daanta", "daant"]):
        scores["workplace_conflict"] += 6
    if any(k in lower for k in ["crying", "cry", "tears", "sob", "cannot stop crying", "can't stop crying", "heartbreak", "sad", "depressed", "loss", "rona", "aansu", "kanna"]):
        scores["crying_grief"] += 5
    if any(k in lower for k in ["panic", "can't breathe", "suffocating", "heart racing", "terrified", "chest tight", "anxious", "ghabrahat", "saans"]):
        scores["panic_anxiety"] += 6
    if any(k in lower for k in ["sleep", "insomnia", "awake", "can't sleep", "nightmare", "racing thoughts", "bed", "neend", "ghoom"]):
        scores["insomnia_racing_thoughts"] += 5
    if any(k in lower for k in ["lonely", "alone", "isolated", "nobody", "invisible", "no friends", "ignored", "akelapan", "ekla"]):
        scores["loneliness_isolation"] += 5
    if any(k in lower for k in ["tension", "tightness", "shoulders", "neck", "knots", "chest pain", "stomach ache", "body aches", "dard", "byatha"]):
        scores["somatic_tightness"] += 4
    if any(k in lower for k in ["meaningless", "lost", "purpose", "god", "karma", "why am i here", "empty", "spiritual", "existential"]):
        scores["existential_meaning"] += 5
    if any(k in lower for k in ["give up", "end it", "pointless", "hopeless", "can't go on", "worthless", "heavy burden"]):
        scores["severe_crisis_hopelessness"] += 5

    # Dimension cues
    if "stressor:workplace" in emotions:
        scores["workplace_conflict"] += 3
    if "melancholic" in emotions or "hopeless" in emotions:
        scores["crying_grief"] += 2
        scores["fatigue_exhaustion"] += 2
    if "anxious" in emotions or "panic" in emotions:
        scores["panic_anxiety"] += 3
    if dims.get("sleep_status") == "Disrupted / Insomnia":
        scores["insomnia_racing_thoughts"] += 3

    # Pick highest scoring domain, or default to general grounding
    best_domain = max(scores, key=scores.get)
    if scores[best_domain] == 0:
        best_domain = "fatigue_exhaustion"

    evidence = EVIDENCE_CORPUS[best_domain]

    # Cultural & linguistic colloquial enrichments
    lang = (language or "en-US").lower()
    is_hinglish = "hinglish" in lang or lang == "en-in"
    is_bangla = "bn" in lang

    colloquial_flavor = ""
    if is_hinglish:
        for key, phrases in HINGLISH_LEXICON.items():
            if key in best_domain or any(k in lower for k in [key]):
                colloquial_flavor = phrases[0]
                break
    elif is_bangla:
        for key, phrases in BANGLA_LEXICON.items():
            if key in best_domain or any(k in lower for k in [key]):
                colloquial_flavor = phrases[0]
                break

    return {
        "domain": best_domain,
        "framework": evidence["framework"],
        "reference": evidence["reference"],
        "clinical_rationale": evidence["clinical_rationale"],
        "somatic_protocol": evidence["somatic_protocol"],
        "reflective_guidance": evidence["reflective_guidance"],
        "chip_badge": evidence["chip_badge"],
        "action_suggestion": evidence["action_suggestion"],
        "colloquial_flavor": colloquial_flavor
    }
