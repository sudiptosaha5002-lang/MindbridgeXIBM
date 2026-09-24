"""
Generates the validated 100-question clinical screening dataset (50 MCQs, 50 VSAQs)
for MindBridge, grounded in the research papers:
- Anxiety.pdf (GAD-7)
- BASELINE SCREENING.pdf (C-SSRS Baseline)
- Q FOR DEPRESSION,ANXIETY.pdf (DASS-21)
- SUICIDE 1.pdf (C-SSRS Recent Self-Report)
- SUICIDE IDENTATION.pdf (Saini et al., 2024 Scoping Review)
- WHO WELLBEING.pdf (WHO-5 Well-Being Index)
- Validated PHQ-9 Depression Screener literature
"""

import json
import os
import sys

def build_questions_100():
    questions = []

    # Helper function to add MCQ
    def add_mcq(qid, text, domain, rule, options, paper, is_safety=False):
        formatted_options = []
        labels = ["A", "B", "C", "D"]
        for idx, opt in enumerate(options):
            lbl = labels[idx] if idx < 4 else chr(65 + idx)
            if isinstance(opt, tuple):
                formatted_options.append({"label": lbl, "text": opt[0], "score": opt[1]})
            elif isinstance(opt, dict):
                formatted_options.append({"label": opt.get("label", lbl), "text": opt["text"], "score": opt.get("score", idx)})
            else:
                formatted_options.append({"label": lbl, "text": str(opt), "score": idx})
        questions.append({
            "question_id": f"q{qid}",
            "question_text": text,
            "question_type": "MCQ",
            "options": formatted_options,
            "domain": domain,
            "scoring_rule": rule,
            "is_safety_question": is_safety,
            "source_paper": paper
        })

    # Helper function to add VSAQ
    def add_vsaq(qid, text, domain, rule, paper, is_safety=False, answer_format="Likert_0_3"):
        questions.append({
            "question_id": f"q{qid}",
            "question_text": text,
            "question_type": "VSAQ",
            "options": None,
            "domain": domain,
            "scoring_rule": rule,
            "is_safety_question": is_safety,
            "source_paper": paper,
            "answer_format": answer_format
        })

    # Standard 4-option Likert for PHQ/GAD/DASS
    likert_4_freq = [
        ("Not at all", 0),
        ("Several days", 1),
        ("More than half the days", 2),
        ("Nearly every day", 3)
    ]

    likert_4_intensity = [
        ("Did not apply to me at all (Never)", 0),
        ("Applied to some degree / occasionally", 1),
        ("Applied to a considerable degree / often", 2),
        ("Applied very much / almost constantly", 3)
    ]

    who5_frequency = [
        ("At no time", 0),
        ("Some of the time", 1),
        ("More than half of the time", 2),
        ("All of the time", 3)
    ]

    # =========================================================================
    # PART 1: 50 MCQs (q1 to q50)
    # =========================================================================

    # --- Domain 1: Mood & Depression (PHQ-9 items 1, 2, 4, 6, 7 + DASS-21 Depression) ---
    add_mcq(1, "Over the last two weeks, how often have you had little interest or pleasure in doing things?", 
            "mood", "phq9_item_1", likert_4_freq, "BASELINE SCREENING.pdf & PHQ-9 Literature (Item 1 Anhedonia)")
    
    add_mcq(2, "Over the last two weeks, how often have you felt down, depressed, or hopeless?", 
            "mood", "phq9_item_2", likert_4_freq, "BASELINE SCREENING.pdf & PHQ-9 Literature (Item 2 Depressed Mood)")
    
    add_mcq(3, "Over the last two weeks, how often have you felt tired or had little energy?", 
            "mood", "phq9_item_4", likert_4_freq, "BASELINE SCREENING.pdf & PHQ-9 Literature (Item 4 Fatigue)")

    add_mcq(4, "Over the last two weeks, how often have you felt bad about yourself — or that you are a failure or have let yourself or your family down?", 
            "mood", "phq9_item_6", likert_4_freq, "BASELINE SCREENING.pdf & PHQ-9 Literature (Item 6 Guilt/Worthlessness)")

    add_mcq(5, "Over the last two weeks, how often have you had trouble concentrating on things, such as reading or working?", 
            "mood", "phq9_item_7", likert_4_freq, "BASELINE SCREENING.pdf & PHQ-9 Literature (Item 7 Concentration)")

    add_mcq(6, "Over the past week, how much did you feel that you couldn't seem to experience any positive feeling at all?", 
            "mood", "dass21_dep_positive_affect", likert_4_intensity, "Q FOR DEPRESSION,ANXIETY.pdf (DASS-21 Item 3)")

    add_mcq(7, "Over the past week, how much did you feel that you had nothing to look forward to?", 
            "mood", "dass21_dep_hopelessness", likert_4_intensity, "Q FOR DEPRESSION,ANXIETY.pdf (DASS-21 Item 10)")

    add_mcq(8, "Over the past week, how much did you feel down-hearted and blue?", 
            "mood", "dass21_dep_blue", likert_4_intensity, "Q FOR DEPRESSION,ANXIETY.pdf (DASS-21 Item 13)")

    add_mcq(9, "Over the past week, how much did you feel that you weren't worth much as a person?", 
            "mood", "dass21_dep_self_worth", likert_4_intensity, "Q FOR DEPRESSION,ANXIETY.pdf (DASS-21 Item 17)")

    add_mcq(10, "Over the past two weeks, how often have you felt cheerful and in good spirits?", 
            "mood", "who5_cheerful", [("At no time", 3), ("Some of the time", 2), ("More than half the time", 1), ("All of the time", 0)], "WHO WELLBEING.pdf (WHO-5 Item 1)")

    # --- Domain 2: Anxiety & Worry (GAD-7 items 1, 2, 3, 4 + DASS-21 Anxiety) ---
    add_mcq(11, "Over the last two weeks, how often have you been bothered by feeling nervous, anxious, or on edge?", 
            "anxiety", "gad7_item_1", likert_4_freq, "Anxiety.pdf (GAD-7 Item 1 Nervousness)")

    add_mcq(12, "Over the last two weeks, how often have you not been able to stop or control worrying?", 
            "anxiety", "gad7_item_2", likert_4_freq, "Anxiety.pdf (GAD-7 Item 2 Uncontrollable Worry)")

    add_mcq(13, "Over the last two weeks, how often have you worried too much about different things?", 
            "anxiety", "gad7_item_3", likert_4_freq, "Anxiety.pdf (GAD-7 Item 3 Excessive Worry)")

    add_mcq(14, "Over the last two weeks, how often have you had trouble relaxing?", 
            "anxiety", "gad7_item_4", likert_4_freq, "Anxiety.pdf (GAD-7 Item 4 Trouble Relaxing)")

    add_mcq(15, "Over the past week, how aware were you of dryness in your mouth or somatic tension?", 
            "anxiety", "dass21_anx_dry_mouth", likert_4_intensity, "Q FOR DEPRESSION,ANXIETY.pdf (DASS-21 Item 2)")

    add_mcq(16, "Over the past week, how often did you experience breathing difficulty (e.g., excessively rapid breathing in the absence of physical exertion)?", 
            "anxiety", "dass21_anx_breathing", likert_4_intensity, "Q FOR DEPRESSION,ANXIETY.pdf (DASS-21 Item 4)")

    add_mcq(17, "Over the past week, how often did you experience trembling or shakiness in your hands?", 
            "anxiety", "dass21_anx_trembling", likert_4_intensity, "Q FOR DEPRESSION,ANXIETY.pdf (DASS-21 Item 7)")

    add_mcq(18, "Over the past week, how often did you feel worried about situations in which you might panic and make a fool of yourself?", 
            "anxiety", "dass21_anx_panic_worry", likert_4_intensity, "Q FOR DEPRESSION,ANXIETY.pdf (DASS-21 Item 9)")

    # --- Domain 3: Stress & Coping (DASS-21 Stress subscale) ---
    add_mcq(19, "Over the past week, how often did you find it hard to wind down after a demanding day?", 
            "stress", "dass21_stress_wind_down", likert_4_intensity, "Q FOR DEPRESSION,ANXIETY.pdf (DASS-21 Item 1)")

    add_mcq(20, "Over the past week, how often did you tend to over-react to unexpected situations?", 
            "stress", "dass21_stress_overreact", likert_4_intensity, "Q FOR DEPRESSION,ANXIETY.pdf (DASS-21 Item 6)")

    add_mcq(21, "Over the past week, how often did you feel that you were burning a lot of nervous energy?", 
            "stress", "dass21_stress_nervous_energy", likert_4_intensity, "Q FOR DEPRESSION,ANXIETY.pdf (DASS-21 Item 8)")

    add_mcq(22, "Over the past week, how often did you find yourself getting agitated or irritable with minor delays?", 
            "stress", "dass21_stress_agitated", likert_4_intensity, "Q FOR DEPRESSION,ANXIETY.pdf (DASS-21 Item 11)")

    add_mcq(23, "Over the past week, how often were you intolerant of anything that kept you from getting on with what you were doing?", 
            "stress", "dass21_stress_intolerant", likert_4_intensity, "Q FOR DEPRESSION,ANXIETY.pdf (DASS-21 Item 14)")

    add_mcq(24, "Over the past week, how often did you feel touchy, sensitive, or easily provoked?", 
            "stress", "dass21_stress_touchy", likert_4_intensity, "Q FOR DEPRESSION,ANXIETY.pdf (DASS-21 Item 18)")

    add_mcq(25, "When feeling intensely stressed, what describes your primary coping response?", 
            "stress", "coping_response_pattern", [
                ("I proactively take a calm pause or practice self-care", 0),
                ("I tend to push through while feeling internal tension", 1),
                ("I withdraw from people and delay tasks", 2),
                ("I feel overwhelmed and struggle to cope", 3)
            ], "SUICIDE IDENTATION.pdf (Saini et al., 2024 Coping Mechanisms)")

    add_mcq(26, "Over the past two weeks, how often have you felt calm and relaxed?", 
            "stress", "who5_calm_relaxed", [("All of the time", 0), ("More than half the time", 1), ("Some of the time", 2), ("At no time", 3)], "WHO WELLBEING.pdf (WHO-5 Item 2)")

    # --- Domain 4: Sleep & Rest (PHQ-9 Item 3 + WHO-5 + Insomnia features) ---
    add_mcq(27, "Over the last two weeks, how often have you had trouble falling or staying asleep, or sleeping too much?", 
            "sleep", "phq9_item_3", likert_4_freq, "BASELINE SCREENING.pdf & PHQ-9 Literature (Item 3 Sleep Disturbance)")

    add_mcq(28, "Over the past two weeks, how often did you wake up feeling fresh and fully rested?", 
            "sleep", "who5_rested_sleep", [("All of the time", 0), ("More than half the time", 1), ("Some of the time", 2), ("At no time", 3)], "WHO WELLBEING.pdf (WHO-5 Item 4)")

    add_mcq(29, "How long does it typically take you to fall asleep after getting into bed at night?", 
            "sleep", "sleep_onset_latency", [
                ("Under 20 minutes (normal onset)", 0),
                ("20 to 45 minutes (mild delay)", 1),
                ("45 to 90 minutes (moderate insomnia)", 2),
                ("More than 90 minutes / severe difficulty", 3)
            ], "SUICIDE IDENTATION.pdf & WHO WELLBEING.pdf (Sleep Disturbance)")

    add_mcq(30, "How frequently do you wake up in the middle of the night or early morning unable to get back to sleep?", 
            "sleep", "sleep_fragmentation", [
                ("Rarely or never", 0),
                ("1 or 2 nights per week", 1),
                ("3 to 5 nights per week", 2),
                ("Almost every single night", 3)
            ], "SUICIDE IDENTATION.pdf & PHQ-9 Literature")

    add_mcq(31, "During daytime hours, how significantly does sleepiness or mental fatigue impact your alertness?", 
            "sleep", "daytime_somnolence", [
                ("No noticeable daytime drowsiness", 0),
                ("Mild afternoon tiredness but manageable", 1),
                ("Frequent sluggishness affecting attention", 2),
                ("Severe exhaustion requiring multiple rests", 3)
            ], "WHO WELLBEING.pdf & PHQ-9 Literature")

    add_mcq(32, "How would you describe the overall restorative quality of your sleep over the past week?", 
            "sleep", "sleep_restorative_quality", [
                ("Deep, peaceful, and restorative", 0),
                ("Fair, though occasionally light", 1),
                ("Fragmented and unrestful", 2),
                ("Completely unrefreshing / exhausting", 3)
            ], "WHO WELLBEING.pdf (WHO-5 Restorative Quality)")

    add_mcq(33, "Over the past month, have unsettling dreams, nightmares, or night awakenings caused noticeable distress?", 
            "sleep", "sleep_nightmare_distress", [
                ("Not at all", 0),
                ("Once or twice a month", 1),
                ("Once or twice a week", 2),
                ("Several times each week", 3)
            ], "SUICIDE IDENTATION.pdf (Saini et al., 2024 Insomnia & Night Sweats)")

    # --- Domain 5: Daily Functioning & Routine ---
    add_mcq(34, "Over the past two weeks, how difficult have any emotional problems made it for you to do your work, take care of things at home, or get along with people?", 
            "functioning", "phq_functional_difficulty", [
                ("Not difficult at all", 0),
                ("Somewhat difficult", 1),
                ("Very difficult", 2),
                ("Extremely difficult", 3)
            ], "BASELINE SCREENING.pdf & PHQ-9 Functional Impairment")

    add_mcq(35, "Over the past two weeks, how often was your daily life filled with things that interest you?", 
            "functioning", "who5_daily_interest", [("All of the time", 0), ("More than half the time", 1), ("Some of the time", 2), ("At no time", 3)], "WHO WELLBEING.pdf (WHO-5 Item 5)")

    add_mcq(36, "How much difficulty have you experienced in initiating and completing your essential daily responsibilities?", 
            "functioning", "executive_inertia", [
                ("No difficulty starting tasks", 0),
                ("Occasional procrastination but completed", 1),
                ("Noticeable struggle to mobilize effort", 2),
                ("Significant inability to initiate basic tasks", 3)
            ], "Q FOR DEPRESSION,ANXIETY.pdf (DASS-21 Item 5 Inertia)")

    add_mcq(37, "How would you describe your engagement with social connections, family, and colleagues over the past two weeks?", 
            "functioning", "social_connectedness_functioning", [
                ("Active, warm, and meaningful engagement", 0),
                ("Mild withdrawal but still connected", 1),
                ("Selective isolation and avoiding conversations", 2),
                ("Complete social withdrawal and isolation", 3)
            ], "SUICIDE IDENTATION.pdf (Saini et al., 2024 Social Isolation)")

    add_mcq(38, "Have changes in your physical health or chronic body discomfort hindered your daily activities recently?", 
            "functioning", "physical_health_impairment", [
                ("Not hindered at all", 0),
                ("Mildly noticeable on certain days", 1),
                ("Moderately limiting work or routines", 2),
                ("Significantly debilitating", 3)
            ], "SUICIDE IDENTATION.pdf (Saini et al., 2024 Physical Health & Pain)")

    add_mcq(39, "Over the past week, how often have you felt enthusiastic about activities you usually participate in?", 
            "functioning", "functional_enthusiasm", [
                ("Consistently enthusiastic", 0),
                ("Enthusiastic about certain projects", 1),
                ("Struggling to find enthusiasm", 2),
                ("Completely unable to feel enthusiastic", 3)
            ], "Q FOR DEPRESSION,ANXIETY.pdf (DASS-21 Item 16)")

    # --- Domain 6: Safety & Risk (MCQs 40 to 45 - All with is_safety_question: True) ---
    add_mcq(40, "In the past month, have you wished you were dead or wished you could go to sleep and not wake up?", 
            "safety", "cssrs_wish_to_be_dead", [
                ("No, never had this wish", 0),
                ("A fleeting thought that passed immediately", 1),
                ("Yes, I have wished this on some days", 2),
                ("Yes, I frequently or strongly wish this", 3)
            ], "SUICIDE 1.pdf (C-SSRS Item 1) & BASELINE SCREENING.pdf", is_safety=True)

    add_mcq(41, "In the past month, have you actually had any thoughts of killing yourself?", 
            "safety", "cssrs_active_ideation", [
                ("No, not at all", 0),
                ("Brief passive thought without desire", 1),
                ("Yes, active thoughts have occurred", 2),
                ("Yes, frequent active thoughts of ending my life", 3)
            ], "SUICIDE 1.pdf (C-SSRS Item 2) & BASELINE SCREENING.pdf", is_safety=True)

    add_mcq(42, "Have you been thinking about a specific way or method you might use to hurt or end your life?", 
            "safety", "cssrs_suicide_method", [
                ("No, no thoughts of any method", 0),
                ("Vague idea with no specific plan or intent to act", 1),
                ("Yes, thought of a method without worked out details", 2),
                ("Yes, concrete method and details formulated", 3)
            ], "SUICIDE 1.pdf (C-SSRS Item 3) & BASELINE SCREENING.pdf", is_safety=True)

    add_mcq(43, "Have you had any intention of acting on thoughts of ending your life, as opposed to having thoughts you would never act on?", 
            "safety", "cssrs_suicide_intent", [
                ("No intent whatsoever to act", 0),
                ("Definite thoughts that I would never act upon", 0),
                ("Unsure whether I might act on them", 2),
                ("Yes, clear intention to act upon them", 3)
            ], "SUICIDE 1.pdf (C-SSRS Item 4) & BASELINE SCREENING.pdf", is_safety=True)

    add_mcq(44, "Have you started to work out or worked out the details of how to kill yourself, with intent to carry out this plan?", 
            "safety", "cssrs_suicide_plan", [
                ("No plan worked out", 0),
                ("General thought without planning details", 1),
                ("Have begun thinking of timing or place", 2),
                ("Yes, specific plan worked out with intent to carry it out", 3)
            ], "SUICIDE 1.pdf (C-SSRS Item 5) & BASELINE SCREENING.pdf", is_safety=True)

    add_mcq(45, "Do you currently have immediate access to lethal means, medications, or instruments that could cause severe self-harm?", 
            "safety", "safety_means_access", [
                ("No access to harmful means", 0),
                ("Normal household items with no harmful intention", 0),
                ("Means available nearby which causes me concern", 2),
                ("Yes, immediate ready access to lethal means with intention", 3)
            ], "SUICIDE IDENTATION.pdf (Saini et al., 2024 Lethal Means Access)", is_safety=True)

    # --- Domain 7: Protective Factors & Hope (MCQs 46 to 50) ---
    add_mcq(46, "When you face emotional distress, how supported do you feel by friends, family, or your community?", 
            "protective", "protective_social_support", [
                ("Strongly supported by caring people", 0),
                ("Somewhat supported by one or two people", 1),
                ("Limited support; often feel alone", 2),
                ("Completely unsupported and isolated", 3)
            ], "SUICIDE IDENTATION.pdf (Saini et al., 2024 Social Support & Buffers)")

    add_mcq(47, "What represents the strongest anchor or reason for continuing forward when life feels difficult?", 
            "protective", "protective_reasons_for_living", [
                ("Loved ones, family, pets, or personal aspirations", 0),
                ("Personal sense of responsibility or curiosity about the future", 1),
                ("Faith, personal values, or commitments", 1),
                ("Currently struggling to identify anchors", 3)
            ], "BASELINE SCREENING.pdf & SUICIDE IDENTATION.pdf")

    add_mcq(48, "How open do you feel toward speaking with a licensed mental health professional or counselor?", 
            "protective", "protective_help_seeking_readiness", [
                ("Very open and willing to seek guidance", 0),
                ("Open if given clear, confidential support", 0),
                ("Hesitant due to stigma or uncertainty", 1),
                ("Reluctant or feeling unready right now", 2)
            ], "SUICIDE IDENTATION.pdf (Saini et al., 2024 Help-Seeking Attitudes)")

    add_mcq(49, "When you recall past challenges you have overcome, how confident are you in your internal resilience?", 
            "protective", "protective_resilience_belief", [
                ("High confidence in my ability to recover", 0),
                ("Moderate confidence with support", 1),
                ("Low confidence; currently feeling drained", 2),
                ("Feel that my coping abilities are depleted", 3)
            ], "WHO WELLBEING.pdf & SUICIDE IDENTATION.pdf")

    add_mcq(50, "Do you have a trusted person or safe space you can reach out to in a moment of distress?", 
            "protective", "protective_safe_person", [
                ("Yes, someone I can contact anytime", 0),
                ("Yes, though I might hesitate to reach out", 1),
                ("Uncertain who would be available", 2),
                ("No safe contact or place currently", 3)
            ], "SUICIDE IDENTATION.pdf (Saini et al., 2024 Trusted Contacts)")

    # =========================================================================
    # PART 2: 50 VSAQs (q51 to q100)
    # =========================================================================

    # --- Domain 1: Mood & Depressive Symptoms (PHQ-9 items 5, 8, 9 + WHO-5 + DASS-21) ---
    add_vsaq(51, "Over the last two weeks, how often have you had poor appetite or found yourself overeating? (0: Not at all, 1: Several days, 2: More than half the days, 3: Nearly every day)",
             "mood", "phq9_item_5", "BASELINE SCREENING.pdf & PHQ-9 Literature (Item 5 Appetite)", answer_format="Likert_0_3")

    add_vsaq(52, "Over the last two weeks, have you noticed moving or speaking so slowly that other people noticed, or being unusually fidgety and restless? (0: Not at all, 1: Several days, 2: More than half the days, 3: Nearly every day)",
             "mood", "phq9_item_8", "BASELINE SCREENING.pdf & PHQ-9 Literature (Item 8 Psychomotor)", answer_format="Likert_0_3")

    add_vsaq(53, "Over the last two weeks, how often have you felt active and vigorous throughout your day? (0: All the time, 1: More than half the time, 2: Some of the time, 3: At no time)",
             "mood", "who5_active_vigorous", "WHO WELLBEING.pdf (WHO-5 Item 3 Vitality)", answer_format="Likert_0_3")

    add_vsaq(54, "Over the past week, did you find it difficult to work up the initiative to do things? (0: Did not apply, 1: Applied somewhat, 2: Applied considerably, 3: Applied very much)",
             "mood", "dass21_dep_initiative", "Q FOR DEPRESSION,ANXIETY.pdf (DASS-21 Item 5)", answer_format="Likert_0_3")

    add_vsaq(55, "Over the past week, did you feel that life was meaningless or devoid of purpose? (0: Did not apply, 1: Applied somewhat, 2: Applied considerably, 3: Applied very much)",
             "mood", "dass21_dep_meaningless", "Q FOR DEPRESSION,ANXIETY.pdf (DASS-21 Item 21)", answer_format="Likert_0_3")

    add_vsaq(56, "When you wake up in the morning, do you experience a persistent feeling of emotional heaviness? (Answer: Yes / No)",
             "mood", "mood_morning_heaviness", "PHQ-9 Literature & DASS-21", answer_format="yes_no")

    add_vsaq(57, "Have you found yourself crying or feeling tearful without an identifiable reason recently? (Answer: Yes / No)",
             "mood", "mood_tearfulness", "DASS-21 Depression Clinical Probes", answer_format="yes_no")

    add_vsaq(58, "In one or two words, how would you describe your overall mood over the past few days? (e.g., calm, exhausted, hopeful, drained)",
             "mood", "mood_descriptor_word", "WHO WELLBEING.pdf (Qualitative Affect)", answer_format="short_text")

    # --- Domain 2: Anxiety & Somatic Arousal (GAD-7 items 5, 6, 7 + DASS-21) ---
    add_vsaq(59, "Over the last two weeks, how often have you been so restless that it is hard to sit still? (0: Not at all, 1: Several days, 2: More than half the days, 3: Nearly every day)",
             "anxiety", "gad7_item_5", "Anxiety.pdf (GAD-7 Item 5 Restlessness)", answer_format="Likert_0_3")

    add_vsaq(60, "Over the last two weeks, how often have you become easily annoyed or irritable? (0: Not at all, 1: Several days, 2: More than half the days, 3: Nearly every day)",
             "anxiety", "gad7_item_6", "Anxiety.pdf (GAD-7 Item 6 Irritability)", answer_format="Likert_0_3")

    add_vsaq(61, "Over the last two weeks, how often have you felt afraid, as if something awful might happen? (0: Not at all, 1: Several days, 2: More than half the days, 3: Nearly every day)",
             "anxiety", "gad7_item_7", "Anxiety.pdf (GAD-7 Item 7 Dread/Fear)", answer_format="Likert_0_3")

    add_vsaq(62, "Over the past week, how close did you feel to panic or losing control? (0: Not at all, 1: Sometimes, 2: Often, 3: Most of the time)",
             "anxiety", "dass21_anx_panic_feeling", "Q FOR DEPRESSION,ANXIETY.pdf (DASS-21 Item 15)", answer_format="Likert_0_3")

    add_vsaq(63, "Over the past week, did you notice rapid or pounding heartbeats when not exercising? (0: Not at all, 1: Sometimes, 2: Often, 3: Most of the time)",
             "anxiety", "dass21_anx_heart_rate", "Q FOR DEPRESSION,ANXIETY.pdf (DASS-21 Item 19)", answer_format="Likert_0_3")

    add_vsaq(64, "Over the past week, did you feel scared without any good reason? (0: Not at all, 1: Sometimes, 2: Often, 3: Most of the time)",
             "anxiety", "dass21_anx_unfounded_fear", "Q FOR DEPRESSION,ANXIETY.pdf (DASS-21 Item 20)", answer_format="Likert_0_3")

    add_vsaq(65, "Do sudden unexpected noises or surprises cause you to startle excessively? (Answer: Yes / No)",
             "anxiety", "anxiety_startle_response", "Anxiety.pdf & DASS-21", answer_format="yes_no")

    add_vsaq(66, "Do you frequently experience tightness in your jaw, shoulders, or chest from muscle tension? (Answer: Yes / No)",
             "anxiety", "anxiety_muscle_tension", "Anxiety.pdf & DASS-21 Somatic Arousal", answer_format="yes_no")

    # --- Domain 3: Stress, Overwhelm & Cognitive Burnout ---
    add_vsaq(67, "Over the past week, did you find it difficult to relax when trying to unwind? (0: Did not apply, 1: Applied somewhat, 2: Applied considerably, 3: Applied very much)",
             "stress", "dass21_stress_difficult_relax", "Q FOR DEPRESSION,ANXIETY.pdf (DASS-21 Item 12)", answer_format="Likert_0_3")

    add_vsaq(68, "On a scale of 0 to 10, what is your average perceived stress level during a typical working day?",
             "stress", "stress_scale_numeric_0_10", "Q FOR DEPRESSION,ANXIETY.pdf (DASS-21 Stress Dimension)", answer_format="numeric_0_10")

    add_vsaq(69, "Do you frequently feel like your thoughts are racing so fast that you cannot keep up? (Answer: Yes / No)",
             "stress", "stress_racing_thoughts", "Q FOR DEPRESSION,ANXIETY.pdf & Anxiety.pdf", answer_format="yes_no")

    add_vsaq(70, "Do you feel mentally exhausted before your work day or study hours even start? (Answer: Yes / No)",
             "stress", "stress_anticipatory_burnout", "Q FOR DEPRESSION,ANXIETY.pdf (Stress/Exhaustion)", answer_format="yes_no")

    add_vsaq(71, "Do unexpected schedule changes or small interruptions trigger immediate irritation? (Answer: Yes / No)",
             "stress", "stress_frustration_threshold", "Q FOR DEPRESSION,ANXIETY.pdf (DASS-21 Item 14 Intolerance)", answer_format="yes_no")

    add_vsaq(72, "In a brief sentence, what is currently the biggest source of stress in your daily life? (e.g., workload, family, health, uncertainty)",
             "stress", "stress_primary_stressor_text", "SUICIDE IDENTATION.pdf (Saini et al., 2024 Life Events)", answer_format="short_text")

    add_vsaq(73, "Do you feel like you have enough personal boundary time each week to decompress? (Answer: Yes / No)",
             "stress", "stress_boundary_rest_adequacy", "WHO WELLBEING.pdf (Rest & Regeneration)", answer_format="yes_no")

    add_vsaq(74, "Have you noticed changes in your digestion, stomach aches, or headaches related to mental stress? (Answer: Yes / No)",
             "stress", "stress_somatic_somatization", "SUICIDE IDENTATION.pdf (Saini et al., 2024 Physical Symptoms)", answer_format="yes_no")

    # --- Domain 4: Sleep & Physical Rest ---
    add_vsaq(75, "On average, approximately how many hours of actual sleep do you get per night? (e.g., 6.5)",
             "sleep", "sleep_average_hours", "WHO WELLBEING.pdf & PHQ-9 (Sleep Duration)", answer_format="numeric_hours")

    add_vsaq(76, "Do you rely on caffeine, energy drinks, or medication to stay awake throughout the day? (Answer: Yes / No)",
             "sleep", "sleep_stimulant_dependency", "SUICIDE IDENTATION.pdf (Saini et al., 2024 Sleep & Substances)", answer_format="yes_no")

    add_vsaq(77, "Do you frequently wake up earlier in the morning than desired without being able to return to sleep? (Answer: Yes / No)",
             "sleep", "sleep_early_morning_awakening", "BASELINE SCREENING.pdf & PHQ-9 Sleep Disturbances", answer_format="yes_no")

    add_vsaq(78, "Do you regularly sleep more than 10 hours a day and still wake up feeling completely fatigued? (Answer: Yes / No)",
             "sleep", "sleep_hypersomnia_fatigue", "PHQ-9 Literature (Hypersomnia)", answer_format="yes_no")

    add_vsaq(79, "Do you find yourself ruminating or worrying about past or future events while lying in bed? (Answer: Yes / No)",
             "sleep", "sleep_bedtime_rumination", "Anxiety.pdf & Q FOR DEPRESSION,ANXIETY.pdf", answer_format="yes_no")

    add_vsaq(80, "How satisfied are you with your current sleep pattern overall? (0: Very dissatisfied, 1: Dissatisfied, 2: Satisfied, 3: Very satisfied)",
             "sleep", "sleep_overall_satisfaction", "WHO WELLBEING.pdf (Sleep Quality Metric)", answer_format="Likert_0_3")

    add_vsaq(81, "Have you noticed difficulty staying awake while driving, working, or sitting in meetings? (Answer: Yes / No)",
             "sleep", "sleep_severe_somnolence_risk", "SUICIDE IDENTATION.pdf & WHO WELLBEING.pdf", answer_format="yes_no")

    # --- Domain 5: Daily Functioning & Routine ---
    add_vsaq(82, "Have you missed work, school, or important responsibilities in the past month due to emotional distress? (Answer: Yes / No)",
             "functioning", "functioning_absenteeism", "BASELINE SCREENING.pdf & SUICIDE IDENTATION.pdf", answer_format="yes_no")

    add_vsaq(83, "Are you able to maintain basic daily self-care routines, such as bathing, meals, and hydration? (Answer: Yes / No)",
             "functioning", "functioning_basic_self_care", "BASELINE SCREENING.pdf (Daily Living Activities)", answer_format="yes_no")

    add_vsaq(84, "Have friends or loved ones expressed concern about your recent withdrawal or mood changes? (Answer: Yes / No)",
             "functioning", "functioning_others_concern", "SUICIDE IDENTATION.pdf (Saini et al., 2024 Social Feedback)", answer_format="yes_no")

    add_vsaq(85, "Do you find yourself procrastinating on simple tasks until they become emergencies? (Answer: Yes / No)",
             "functioning", "functioning_procrastination_stress", "Q FOR DEPRESSION,ANXIETY.pdf (Inertia)", answer_format="yes_no")

    add_vsaq(86, "How much does emotional fatigue hinder your ability to make clear decisions? (0: None, 1: Mild, 2: Moderate, 3: Severe)",
             "functioning", "functioning_decision_making", "PHQ-9 Literature (Concentration & Indecisiveness)", answer_format="Likert_0_3")

    add_vsaq(87, "Are you able to enjoy downtime or hobbies when you have free time? (Answer: Yes / No)",
             "functioning", "functioning_recreational_anhedonia", "WHO WELLBEING.pdf & PHQ-9 Item 1", answer_format="yes_no")

    # --- Domain 6: Safety, Risk & Escalation (VSAQs 88 to 94 - All with is_safety_question: True) ---
    add_vsaq(88, "Over the last two weeks, how often have you had thoughts that you would be better off dead, or of hurting yourself in some way? (0: Not at all, 1: Several days, 2: More than half the days, 3: Nearly every day)",
             "safety", "phq9_item_9_suicidality", "BASELINE SCREENING.pdf & PHQ-9 Literature (Item 9 Self-Harm)", is_safety=True, answer_format="Likert_0_3")

    add_vsaq(89, "Have you ever done anything, started to do anything, or prepared to do anything to end your life? (Answer: Yes / No)",
             "safety", "cssrs_suicidal_behavior", "SUICIDE 1.pdf (C-SSRS Item 6) & BASELINE SCREENING.pdf", is_safety=True, answer_format="yes_no")

    add_vsaq(90, "If you answered yes to past self-harm or attempts, did this behavior occur within the past 3 months? (Answer: Yes / No / Not Applicable)",
             "safety", "cssrs_recent_attempt_3mo", "SUICIDE 1.pdf (C-SSRS Recent Behavior Probe)", is_safety=True, answer_format="yes_no")

    add_vsaq(91, "Have you engaged in any deliberate self-injury or cutting without intent to die in the past month? (Answer: Yes / No)",
             "safety", "safety_non_suicidal_self_injury", "BASELINE SCREENING.pdf & Saini et al., 2024 (Non-Suicidal Self-Injury)", is_safety=True, answer_format="yes_no")

    add_vsaq(92, "Are you currently experiencing any physical danger, domestic violence, or abuse in your living environment? (Answer: Yes / No)",
             "safety", "safety_domestic_violence_abuse", "SUICIDE IDENTATION.pdf (Saini et al., 2024 Abuse & Domestic Risk)", is_safety=True, answer_format="yes_no")

    add_vsaq(93, "Do you have any active thoughts or urges to harm another person? (Answer: Yes / No)",
             "safety", "safety_harm_to_others", "BASELINE SCREENING.pdf & Clinical Triage Standards", is_safety=True, answer_format="yes_no")

    add_vsaq(94, "Do you feel that you cannot keep yourself safe right now? (Answer: Yes / No)",
             "safety", "safety_cannot_keep_safe", "SUICIDE IDENTATION.pdf (Saini et al., 2024 Imminent Risk Probe)", is_safety=True, answer_format="yes_no")

    # --- Domain 7: Protective Factors & Hope (VSAQs 95 to 100) ---
    add_vsaq(95, "Can you name at least one person you could speak with honestly if you were in severe pain? (Answer: Yes / No)",
             "protective", "protective_confidant_presence", "SUICIDE IDENTATION.pdf (Saini et al., 2024 Social Connection)", answer_format="yes_no")

    add_vsaq(96, "Do you believe that with appropriate psychological care and life changes, your current situation can improve? (Answer: Yes / No)",
             "protective", "protective_optimism_belief", "SUICIDE IDENTATION.pdf & WHO WELLBEING.pdf", answer_format="yes_no")

    add_vsaq(97, "What is one self-care activity or grounding practice that brings you relief when you are stressed? (e.g., walking, music, deep breathing)",
             "protective", "protective_grounding_habit", "WHO WELLBEING.pdf (Grounding Strategies)", answer_format="short_text")

    add_vsaq(98, "Have you ever engaged with a counselor, therapist, or doctor for mental health support in the past? (Answer: Yes / No)",
             "protective", "protective_prior_therapy_experience", "SUICIDE IDENTATION.pdf (Saini et al., 2024 Clinical History)", answer_format="yes_no")

    add_vsaq(99, "Are you currently interested in receiving structured guidance, self-care exercises, or a professional referral? (Answer: Yes / No)",
             "protective", "protective_referral_readiness", "SUICIDE IDENTATION.pdf (Saini et al., 2024 Referral Pathways)", answer_format="yes_no")

    add_vsaq(100, "On a scale from 0 to 10, how motivated do you feel today to take small positive steps for your well-being?",
              "protective", "protective_motivation_score_0_10", "WHO WELLBEING.pdf (Well-being Self-Agency)", answer_format="numeric_0_10")

    return questions

def validate_and_save():
    qs = build_questions_100()

    # Validations
    total = len(qs)
    mcqs = [q for q in qs if q["question_type"] == "MCQ"]
    vsaqs = [q for q in qs if q["question_type"] == "VSAQ"]
    safety_qs = [q for q in qs if q.get("is_safety_question") is True]

    phq9_items = [q for q in qs if "phq9_item" in q.get("scoring_rule", "")]
    gad7_items = [q for q in qs if "gad7_item" in q.get("scoring_rule", "")]

    print(f"Total questions: {total}")
    print(f"MCQs: {len(mcqs)}")
    print(f"VSAQs: {len(vsaqs)}")
    print(f"Safety Questions: {len(safety_qs)}")
    print(f"PHQ-9 Aligned Items: {len(phq9_items)}")
    print(f"GAD-7 Aligned Items: {len(gad7_items)}")

    assert total == 100, f"Expected 100 questions, got {total}"
    assert len(mcqs) == 50, f"Expected 50 MCQs, got {len(mcqs)}"
    assert len(vsaqs) == 50, f"Expected 50 VSAQs, got {len(vsaqs)}"
    assert len(safety_qs) >= 10, f"Expected at least 10 safety questions, got {len(safety_qs)}"
    assert len(phq9_items) >= 9, f"Expected at least 9 PHQ-9 items, got {len(phq9_items)}"
    assert len(gad7_items) >= 7, f"Expected at least 7 GAD-7 items, got {len(gad7_items)}"

    # Check that all MCQs have exactly 4 options with label, text, score
    for mcq in mcqs:
        opts = mcq.get("options")
        assert opts and len(opts) == 4, f"MCQ {mcq['question_id']} must have exactly 4 options"
        for opt in opts:
            assert "label" in opt and "text" in opt and "score" in opt

    # Check domain distribution
    domains = {}
    for q in qs:
        d = q["domain"]
        domains[d] = domains.get(d, 0) + 1
    print("Domain distribution:", domains)

    # Save to multiple canonical locations
    target_paths = [
        os.path.join(os.path.dirname(__file__), "questions_100.json"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "questions_100.json"),
        os.path.join(os.path.dirname(__file__), "data", "questions_100.json")
    ]

    for path in target_paths:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(qs, f, indent=2, ensure_ascii=False)
        print(f"Saved 100 questions to {path}")

if __name__ == "__main__":
    validate_and_save()
