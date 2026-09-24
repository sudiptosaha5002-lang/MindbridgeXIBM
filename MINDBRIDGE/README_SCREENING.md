# MindBridge Research-Grounded Mental Health Screening Module

> **Clinical & Non-Diagnostic Disclaimer**:  
> **This tool does not diagnose mental health conditions.** It helps reflect on your experiences and suggests when speaking with a professional may be helpful. Any high-risk or crisis result must be followed by licensed human professional support.

---

## 1. Research Papers Grounding & Evidence Base

The screening module is strictly grounded in the research papers and clinical instruments located in the `research_paper` (and `backend/research_papers`) directory:

1. **`Anxiety.pdf` — Generalized Anxiety Disorder-7 (GAD-7)**
   - *Authors*: Robert L. Spitzer, Kurt Kroenke, Janet B. W. Williams, Bernd Löwe (2006).
   - *Clinical Construct*: Generalized anxiety, uncontrollable worry, restlessness, somatic tension, trouble relaxing, impending dread.
   - *Scoring*: 7 Likert items (0 to 3), Total score 0–21.
   - *Cutoffs*: 0–4 Minimal, 5–9 Mild, 10–14 Moderate, 15–21 Severe. Score $\ge 10$ has 89% sensitivity and 82% specificity for generalized anxiety.

2. **`BASELINE SCREENING.pdf` & `SUICIDE 1.pdf` — Columbia-Suicide Severity Rating Scale (C-SSRS)**
   - *Authors*: Kelly Posner, David Brent, Christopher Lucas, Madelyn Gould, Barbara Stanley, Gregory Brown, et al.
   - *Clinical Construct*: Suicidal ideation severity (wish to be dead, active ideation, thoughts with method, intent, specific plan) and suicidal behavior/past attempts.
   - *Safety Gate*: Any affirmative response to active suicidal intent, detailed plan, access to lethal means, recent attempts, or severe abuse immediately triggers acute crisis escalation and halts normal screening.

3. **`Q FOR DEPRESSION,ANXIETY.pdf` — Depression, Anxiety and Stress Scale - 21 Items (DASS-21)**
   - *Authors*: P. F. Lovibond & S. H. Lovibond (1995).
   - *Clinical Construct*: 3 subscales of 7 items each:
     - **Depression**: Dysphoria, hopelessness, devaluation of life, lack of initiative, anhedonia.
     - **Anxiety**: Autonomic arousal, skeletal muscle effects, situational panic.
     - **Stress**: Chronic non-specific arousal, difficulty relaxing, nervous agitation, irritability.
   - *Scoring*: 0–3 frequency scale multiplied by 2.

4. **`WHO WELLBEING.pdf` — WHO-5 Well-Being Index**
   - *Origin*: World Health Organization Collaborating Centre for Mental Health.
   - *Clinical Construct*: 5 positively phrased items measuring psychological well-being, positive affect, vitality, and restorative sleep over the past 2 weeks.
   - *Cutoff*: Raw score $< 13$ or percentage $< 50\%$ indicates poor well-being and is a clinically validated indicator for depression screening.

5. **`SUICIDE IDENTATION.pdf` — Primary Care Suicide Risk Factors Scoping Review**
   - *Authors*: Pooja Saini, Anna Hunt, Peter Blaney, Annie Murray (Journal of Prevention, 2024).
   - *Findings*: Critical primary care risk factors: interpersonal isolation, chronic physical pain, substance misuse, domestic violence, disclosure barriers, warm referral pathways, and the protective role of social confidants.

6. **Validated PHQ-9 Literature (Patient Health Questionnaire-9)**
   - *Authors*: Spitzer, Kroenke, Williams et al.
   - *Clinical Construct*: Anhedonia, low mood, sleep disturbance, fatigue, appetite changes, guilt/worthlessness, concentration difficulty, psychomotor changes, thoughts of self-harm.
   - *Scoring*: 9 Likert items (0 to 3), Total score 0–27 (0–4 Minimal, 5–9 Mild, 10–14 Moderate, 15–19 Moderately Severe, 20–27 Severe).

---

## 2. 100-Question Clinical Dataset (`questions_100.json`)

The dataset contains **exactly 100 questions** partitioned into:
- **50 Multiple Choice Questions (MCQs)**: 4 standardized options (A, B, C, D) mapped to clinical severity scores (0 to 3).
- **50 Very Short Answer Questions (VSAQs)**: Short structured answers (Likert 0–3, yes/no, number of hours, or concise reflection text).

### Domain Distribution:
- **Mood & Depressive Spectrum** (18 items): Includes 9 validated PHQ-9 items, DASS-21 Depression items, and WHO-5 positive affect.
- **Anxiety & Somatic Tension** (16 items): Includes 7 validated GAD-7 items and DASS-21 Anxiety items.
- **Stress, Burnout & Coping** (16 items): Includes DASS-21 Stress items and perceived workload/burnout items.
- **Sleep & Physical Rest** (14 items): Sleep onset latency, fragmentation, daytime somnolence, restorative quality.
- **Daily Functioning & Routine** (12 items): Occupational focus, executive inertia, social connectedness.
- **Safety & Risk Assessment** (13 items, $\ge 10$ required): Direct C-SSRS probes, lethal means access, prior attempts, domestic abuse, harm to others. **All 13 trigger immediate crisis escalation if answered affirmatively.**
- **Protective Factors & Hope** (11 items): Social support anchors, reasons for living, therapeutic help-seeking readiness, resilience belief.

---

## 3. Session Shuffling & Per-User Randomization

- For every new screening session, `shuffle_questions_for_user(user_id)` generates a random permutation of the 100 question IDs.
- The order is stored in SQLite (`screening_sessions.question_order`) so that each user experiences a unique order while maintaining session consistency.
- **Position-Independent Safety Detection**: Safety questions are evaluated on every submission regardless of where they appear in the shuffled sequence.

---

## 4. Voice-First Dual-Input Architecture

- **Voice Input (Preferred / Default)**:
  - Prominent pulsating microphone button with audio wave visualizer.
  - Speech captured via browser SpeechRecognition API or backend STT (`/api/voice/transcribe`).
  - **Editable Transcript Review**: Before final submission, the recognized text is displayed in an editable preview field so the user can verify, correct, or refine their answer.
  - The system records both the `raw_transcript` and the final submitted `answer_text` with `input_mode: "voice"`.
- **Text Input**:
  - Interactive 4-option cards for MCQs (A, B, C, D) with hover and selection animations.
  - Quick-response rating chips and text input field for VSAQs.

---

## 5. Non-Diagnostic Scoring & Care Stratification

The scoring engine calculates:
- **PHQ-9 Score (0–27)** & severity band (`minimal`, `mild`, `moderate`, `moderately_severe`, `severe`)
- **GAD-7 Score (0–21)** & severity band (`minimal`, `mild`, `moderate`, `severe`)
- **Stress Score (0–42)** from DASS-21 items
- **Sleep Quality Index** & **Daily Functioning Impairment Index**
- **Overall Distress Tier**: `low`, `moderate`, `high`
- **Risk Flag**: `none`, `moderate`, `high`, `immediate`

### Tiered Recommendations:
- `self_care`: Low distress, no safety concerns. Recommends psychoeducation, audio soundscapes, and sleep hygiene.
- `psychologist_referral`: Mild to moderate distress. Recommends consulting a licensed clinical psychologist.
- `urgent_psychiatrist_referral`: High distress or significant functional disruption. Recommends medical/psychiatric evaluation.
- `crisis_resources`: Immediate safety risk. Halts screening and connects directly to 24/7 crisis hotlines.

---

## 6. Output JSON Schema

```json
{
  "user_id": "patient-maya-voice",
  "session_id": "scr-2df4c90f12",
  "timestamp": "2026-09-17T18:05:08.520141+00:00",
  "phq9_score": 8,
  "phq9_severity": "mild",
  "gad7_score": 7,
  "gad7_severity": "mild",
  "stress_score": 12,
  "sleep_score": 6,
  "functioning_score": 4,
  "overall_distress": "moderate",
  "risk_flag": "none",
  "summary_text": "Your answers suggest that persistent stress, anxious tension, or temporary dips in mood have been affecting your day-to-day rhythm. Sleep quality and daytime energy also show signs of strain. Connecting with a licensed psychologist or professional counselor can provide structured, practical tools for restoring calm and perspective.",
  "recommended_action": "psychologist_referral",
  "question_order": ["q85", "q81", "q92", "q19", "..."],
  "disclaimer": "This tool does not diagnose mental health conditions. It helps reflect on your experiences and suggests when speaking with a professional may be helpful."
}
```

---

## 7. Immediate Crisis Safety Escalation

If any question is answered in a way that indicates active suicidal thoughts, plan, intent, access to means, recent self-harm, or severe abuse:
1. Normal screening questions stop immediately.
2. An emergency crisis overlay is displayed with 24/7 confidential helplines:
   - **Tele-MANAS (Govt of India)**: `14416` / `1800-891-4416` (24/7, 20+ languages)
   - **KIRAN Helpline**: `1800-599-0019` (24/7)
   - **Vandrevala Foundation**: `+91 9999 666 555` (24/7)
   - **988 Suicide & Crisis Lifeline**: `988` (US/Canada)
3. Background soundscapes are silenced to ensure cognitive clarity.
4. A secure crisis audit event is logged in the database (`crisis_flag = 1`).

---

## 8. Running the Demo and Tests

```bash
# Run unit and integration tests (validating all constraints)
python -m unittest tests/test_mental_screening.py

# Run interactive simulation demo
python demo_screener.py
```
