"""
MindBridge Safety and Emergency Protocol Test Suite
"""
import re
from typing import Dict, List, Any

def assess_safety_and_emergency(answers: Dict[str, str], all_text: str = "") -> Dict[str, Any]:
    if not all_text:
        all_text = " ".join([str(v) for v in answers.values() if isinstance(v, str)])
    
    clean_text = all_text.strip().lower()
    clean_text = (
        clean_text.replace("’", "'")
        .replace("‘", "'")
        .replace("`", "'")
        .replace("“", '"')
        .replace("”", '"')
        .replace("—", " ")
        .replace("–", " ")
    )

    if not clean_text:
        return {
            "is_emergency": False,
            "emergency_flags": [],
            "risk_level": "LOW",
            "recommended_action": "CONTINUE_SCREENING",
            "emergency_title": "",
            "emergency_details": "",
            "clinical_protocol_notice": ""
        }

    flags: List[str] = []

    # 1. Suicide and self-harm risk (highest priority)
    # A. Active suicidal ideation with plan and intent
    pat_active_suicide = [
        r"(?=.*\b(kill\s*myself|end\s*my\s*life|commit\s*suicide|suicide|end\s*it\s*all)\b)(?=.*\b(have\s*a\s*plan|know\s*how|soon|tonight|today|decided|ready\s*to\s*die)\b)",
        r"\bi\s*(?:want\s*to|am\s*going\s*to|will|have\s*decided\s*to)\s*(?:kill\s*myself|end\s*my\s*life)\s*(?:soon|tonight|today)?\b",
        r"\bdecided\s*to\s*end\s*my\s*life\s*and\s*i\s*know\s*how\b",
        r"(?=.*\b(mar\s*jana\s*chahta|jaan\s*dena|khudkushi)\b)(?=.*\b(plan\s*hai|khatam|aaj|raat)\b)",
        r"(?=.*(মরতে\s*চাই|জীবন\s*শেষ|আত্মহত্যা\s*করব))(?=.*(পরিকল্পনা|আজ|শীঘ্রই))"
    ]
    if any(re.search(p, clean_text, re.IGNORECASE) for p in pat_active_suicide):
        flags.append("ACTIVE_SUICIDE_WITH_PLAN_AND_INTENT")

    # B. Recent high-lethality suicide attempt
    pat_recent_attempt = [
        r"\b(?:tried\s*to|attempted\s*to)\s*(?:kill\s*myself|end\s*my\s*life|commit\s*suicide)\b",
        r"\battempted\s*suicide\b",
        r"\b(?:took|swallowed)\s*(?:a\s*(?:large|huge)\s*number\s*of|too\s*many|a\s*lot\s*of|lethal|massive\s*amount\s*of)\s*pills\s*(?:to\s*die)?\b",
        r"\b(?:tried|attempted)\s*to\s*(?:hang\s*myself|overdose|jump\s*off|slit\s*my\s*wrists?)\b",
        r"\battempted\s*suicide\s*and\s*needed\s*medical\s*help\b"
    ]
    if any(re.search(p, clean_text, re.IGNORECASE) for p in pat_recent_attempt):
        flags.append("RECENT_HIGH_LETHALITY_ATTEMPT")

    # C. Suicidal ideation + access to lethal means + poor control
    has_suicide_ideation = bool(re.search(r"\b(suicid\w*|want\s*to\s*die|kill\s*myself|end\s*my\s*life|thoughts\s*of\s*dying)\b", clean_text, re.IGNORECASE))
    has_means = bool(re.search(r"\b(pills?|weapons?|gun|knife|blade|heights?|bridge|railway|pesticides?|poison|hanging)\b", clean_text, re.IGNORECASE))
    has_poor_control = bool(re.search(r"\b(poor\s*(?:self[\s\-]*)?control|can'?t\s*control|cannot\s*stop\s*myself|intoxicated|drunk|drinking\s*heavily|high|severe\s*agitation|psychosis|might\s*do\s*it|impulsive|lack\s*of\s*control)\b", clean_text, re.IGNORECASE))
    if has_suicide_ideation and has_means and has_poor_control:
        flags.append("SEVERE_SUICIDAL_IDEATION_WITH_MEANS")

    # D. Command hallucinations or psychosis telling user to harm themselves
    pat_command_hallucination = [
        r"\bvoices?\s*(?:are\s*)?telling\s*me\s*to\s*(?:kill|hurt|harm|cut|end|destroy)\s*myself\b",
        r"\bsomething\s*(?:inside\s*me\s*is\s*)?forcing\s*me\s*to\s*(?:hurt|harm|kill)\s*myself\b",
        r"\bvoices?\s*in\s*my\s*head\s*(?:saying|commanding|telling)\s*me\s*to\s*(?:die|kill\s*myself|harm\s*myself)\b"
    ]
    if any(re.search(p, clean_text, re.IGNORECASE) for p in pat_command_hallucination):
        flags.append("COMMAND_HALLUCINATIONS_TO_SELF_HARM")

    # E. Non-suicidal self-harm with high immediate danger
    pat_active_self_harm = [
        r"\bcutting\s*myself\s*(?:right\s*now|actively)\b",
        r"\bcutting\s*(?:myself)?\s*and\s*cannot\s*stop\b",
        r"\boverdosing\s*on\s*purpose\b",
        r"\bseriously\s*injuring\s*myself\b",
        r"\bneed\s*medical\s*help\s*for\s*(?:bleeding|cuts?|wounds?|burns?)\b"
    ]
    if any(re.search(p, clean_text, re.IGNORECASE) for p in pat_active_self_harm):
        flags.append("UNCONTROLLED_ACTIVE_SELF_HARM")

    # 2. Panic attack / acute anxiety crisis with medical risk
    has_panic_statement = bool(re.search(
        r"(?:panic\s*attack\s*right\s*now|heart\s*is\s*racing.*(?:feel\s*like\s*i'?m\s*dying|can'?t\s*breathe)|feel\s*like\s*i'?m\s*dying\s*and\s*(?:i\s*)?can'?t\s*control|never\s*felt\s*this\s*before.*something\s*is\s*very\s*wrong\s*with\s*my\s*body)",
        clean_text, re.IGNORECASE
    ))
    has_medical_risk = bool(re.search(
        r"(?:severe\s*chest\s*pain|trouble\s*breathing|can'?t\s*breathe|shortness\s*of\s*breath|fainting|passed?\s*out|blacking\s*out|confusion|heart\s*condition|lung\s*condition)",
        clean_text, re.IGNORECASE
    ))
    panic_symptom_patterns = [
        r"\b(palpitations?|racing\s*heart|heart\s*beating\s*fast)\b",
        r"\b(sweating|sweat|cold\s*sweats?)\b",
        r"\b(trembling|shaking)\b",
        r"\b(shortness\s*of\s*breath|choking|can'?t\s*breathe)\b",
        r"\b(chest\s*pain|chest\s*tightness|discomfort\s*in\s*chest)\b",
        r"\b(nausea|abdominal\s*pain|stomach\s*cramps?)\b",
        r"\b(dizziness|light-?headed|faint(?:ness)?)\b",
        r"\b(chills|hot\s*flashes|heat\s*sensations?)\b",
        r"\b(numbness|tingling|pins\s*and\s*needles)\b",
        r"\b(unreal|detached|derealization|depersonalization)\b",
        r"\b(fear\s*of\s*losing\s*control|going\s*crazy)\b",
        r"\b(fear\s*of\s*dying|feel\s*like\s*(?:i'?m\s*)?dying)\b"
    ]
    symptom_count = sum(1 for p in panic_symptom_patterns if re.search(p, clean_text, re.IGNORECASE))
    if (has_panic_statement and has_medical_risk) or (symptom_count >= 3 and has_medical_risk):
        flags.append("ACUTE_PANIC_WITH_MEDICAL_RISK")

    # 3. Acute crisis with inability to care for self
    pat_severe_neglect = [
        r"\bhaven'?t\s*(?:eaten|eaten\s*or\s*drunk)\s*(?:anything)?\s*for\s*days\s*and\s*don'?t\s*care\s*if\s*i\s*live\s*or\s*die\b",
        r"\bso\s*depressed\s*i\s*cannot\s*(?:get\s*out\s*of\s*bed|take\s*care\s*of\s*myself)\b",
        r"\bcompletely\s*hopeless\s*and\s*(?:i\s*)?don'?t\s*think\s*i\s*can\s*stay\s*alive\s*tonight\b",
        r"\balone[,\s]+extremely\s*agitated[,\s]+and\s*i\s*might\s*do\s*something\s*dangerous\b"
    ]
    if any(re.search(p, clean_text, re.IGNORECASE) for p in pat_severe_neglect):
        flags.append("SEVERE_DEPRESSION_WITH_HOPELESSNESS_AND_NO_SELF_CARE")

    # 4. Severe dissociation, psychosis, or loss of reality
    pat_psychosis_danger = [
        r"\bdon'?t\s*know\s*what\s*is\s*real\s*anymore\b",
        r"\bhear\s*voices\s*telling\s*me\s*to\s*hurt\s*(?:myself|others)\b",
        r"\bcompletely\s*detached\s*from\s*my\s*body\s*and\s*i\s*might\s*do\s*something\s*dangerous\b",
        r"\bpeople\s*are\s*watching\s*me\s*and\s*trying\s*to\s*harm\s*me\b"
    ]
    if any(re.search(p, clean_text, re.IGNORECASE) for p in pat_psychosis_danger):
        flags.append("PSYCHOSIS_WITH_DANGER_TO_SELF_OR_OTHERS")

    # 5. Immediate risk of harm to others
    pat_harm_others = [
        r"\bwant\s*to\s*(?:hurt|kill|murder)\s*someone\b",
        r"\bhave\s*a\s*plan\s*to\s*(?:harm|kill|attack)\s*(?:a\s*specific\s*person|someone)\b",
        r"\bmight\s*lose\s*control\s*and\s*attack\s*someone\b"
    ]
    if any(re.search(p, clean_text, re.IGNORECASE) for p in pat_harm_others):
        flags.append("IMMINENT_HARM_TO_OTHERS")

    # 6. Mixed high-risk states
    has_severe_dep = bool(re.search(r"\b(severe\s*depression|deeply\s*depressed|hopeless|cannot\s*live)\b", clean_text, re.IGNORECASE))
    has_substance = bool(re.search(r"\b(heavy\s*(?:drinking|alcohol)|intoxicated|drugs|overdosing|high|substance)\b", clean_text, re.IGNORECASE))
    has_heart_history = bool(re.search(r"\b(history\s*of\s*heart|heart\s*disease|cardiac|previous\s*heart\s*attack)\b", clean_text, re.IGNORECASE))
    
    mixed_danger = (
        (has_severe_dep and has_substance and has_suicide_ideation) or
        (symptom_count >= 2 and has_medical_risk and has_heart_history) or
        ("UNCONTROLLED_ACTIVE_SELF_HARM" in flags and has_substance) or
        ("COMMAND_HALLUCINATIONS_TO_SELF_HARM" in flags and has_suicide_ideation)
    )
    if mixed_danger and "MIXED_HIGH_RISK_STATE" not in flags:
        flags.append("MIXED_HIGH_RISK_STATE")

    is_emergency = len(flags) > 0

    if is_emergency:
        risk_level = "CRISIS"
        recommended_action = "EMERGENCY_MODE"
        title_map = {
            "ACTIVE_SUICIDE_WITH_PLAN_AND_INTENT": "Active Suicidal Ideation with Plan and Intent",
            "RECENT_HIGH_LETHALITY_ATTEMPT": "Recent High-Lethality Suicide Attempt Reported",
            "SEVERE_SUICIDAL_IDEATION_WITH_MEANS": "Severe Suicidal Ideation with Access to Means",
            "COMMAND_HALLUCINATIONS_TO_SELF_HARM": "Command Hallucinations Directing Self-Harm",
            "UNCONTROLLED_ACTIVE_SELF_HARM": "Active Uncontrolled Self-Harm with Immediate Danger",
            "ACUTE_PANIC_WITH_MEDICAL_RISK": "Acute Panic Attack Crisis with Physical / Medical Risk",
            "SEVERE_DEPRESSION_WITH_HOPELESSNESS_AND_NO_SELF_CARE": "Acute Crisis with Inability to Maintain Self-Care / Safety",
            "PSYCHOSIS_WITH_DANGER_TO_SELF_OR_OTHERS": "Severe Dissociation, Psychosis or Loss of Reality",
            "IMMINENT_HARM_TO_OTHERS": "Imminent Danger or Intent of Harm to Others",
            "MIXED_HIGH_RISK_STATE": "Mixed High-Risk Co-Occurring Crisis State"
        }
        primary_title = title_map.get(flags[0], "Critical Risk Threshold Met")
        details = (
            f"Screening reflections triggered safety criteria ({primary_title}). "
            f"Immediate human support, crisis helpline contact, or emergency department evaluation is required."
        )
        protocol_notice = "CRITICAL RISK: Clinical emergency thresholds met. Urgent evaluation required."
    else:
        has_distress = bool(re.search(r"\b(sad|stressed|anxious|tired|exhausted|burnout|overthinking|worried)\b", clean_text, re.IGNORECASE))
        risk_level = "MODERATE" if has_distress else "LOW"
        recommended_action = "CONTINUE_SCREENING"
        primary_title = ""
        details = ""
        protocol_notice = "Standard screening protocol. No acute safety flags detected."

    return {
        "is_emergency": is_emergency,
        "emergency_flags": flags,
        "risk_level": risk_level,
        "recommended_action": recommended_action,
        "emergency_title": primary_title,
        "emergency_details": details,
        "clinical_protocol_notice": protocol_notice
    }

if __name__ == "__main__":
    test_cases = [
        ("I want to kill myself and I have a plan.", True, "ACTIVE_SUICIDE_WITH_PLAN_AND_INTENT"),
        ("I have decided to end my life and I know how I will do it.", True, "ACTIVE_SUICIDE_WITH_PLAN_AND_INTENT"),
        ("I am going to kill myself soon.", True, "ACTIVE_SUICIDE_WITH_PLAN_AND_INTENT"),
        ("I tried to kill myself today by overdose", True, "RECENT_HIGH_LETHALITY_ATTEMPT"),
        ("I took a large number of pills to die.", True, "RECENT_HIGH_LETHALITY_ATTEMPT"),
        ("I attempted suicide and needed medical help.", True, "RECENT_HIGH_LETHALITY_ATTEMPT"),
        ("I have frequent intense suicidal thoughts, I have pills and weapons, and poor self-control.", True, "SEVERE_SUICIDAL_IDEATION_WITH_MEANS"),
        ("Voices are telling me to kill myself.", True, "COMMAND_HALLUCINATIONS_TO_SELF_HARM"),
        ("Something inside me is forcing me to hurt myself.", True, "COMMAND_HALLUCINATIONS_TO_SELF_HARM"),
        ("I am cutting myself right now and cannot stop.", True, "UNCONTROLLED_ACTIVE_SELF_HARM"),
        ("I am overdosing on purpose to hurt myself.", True, "UNCONTROLLED_ACTIVE_SELF_HARM"),
        ("I am seriously injuring myself and may need medical help.", True, "UNCONTROLLED_ACTIVE_SELF_HARM"),
        ("I think I’m having a panic attack right now and I can’t breathe, with severe chest pain.", True, "ACUTE_PANIC_WITH_MEDICAL_RISK"),
        ("My heart is racing, I feel like I’m dying, and I can’t control it, trouble breathing.", True, "ACUTE_PANIC_WITH_MEDICAL_RISK"),
        ("I haven’t eaten or drunk anything for days and don’t care if I live or die.", True, "SEVERE_DEPRESSION_WITH_HOPELESSNESS_AND_NO_SELF_CARE"),
        ("I am so depressed I cannot get out of bed or take care of myself.", True, "SEVERE_DEPRESSION_WITH_HOPELESSNESS_AND_NO_SELF_CARE"),
        ("I feel completely hopeless and I don't think I can stay alive tonight.", True, "SEVERE_DEPRESSION_WITH_HOPELESSNESS_AND_NO_SELF_CARE"),
        ("I don’t know what is real anymore.", True, "PSYCHOSIS_WITH_DANGER_TO_SELF_OR_OTHERS"),
        ("I want to kill someone, I have a plan to harm a specific person.", True, "IMMINENT_HARM_TO_OTHERS"),
        # Negative cases
        ("I feel a bit sad today because of exam pressure and poor sleep.", False, None),
        ("I get stressed when work deadlines approach, but I manage with walks.", False, None),
        ("I miss my grandfather who passed away two years ago, but I have good friends.", False, None)
    ]

    all_passed = True
    for text, exp_emerg, exp_flag in test_cases:
        res = assess_safety_and_emergency({}, text)
        flag_match = (exp_flag in res["emergency_flags"]) if exp_flag else (len(res["emergency_flags"]) == 0)
        passed = (res["is_emergency"] == exp_emerg) and flag_match
        if not passed:
            all_passed = False
            print(f"FAILED: '{text}' -> Got emerg={res['is_emergency']}, flags={res['emergency_flags']}, expected emerg={exp_emerg}, flag={exp_flag}")
        else:
            print(f"PASSED: '{text[:45]}...' -> emerg={res['is_emergency']}, flags={res['emergency_flags']}")

    if all_passed:
        print("\nALL 22 UNIT TESTS PASSED PERFECTLY!")
