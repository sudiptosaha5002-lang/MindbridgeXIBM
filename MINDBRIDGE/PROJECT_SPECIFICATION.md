# MindBridge: Clinical AI Screening & Safe Care-Navigation Architecture

> **Notice & Non-Diagnostic Disclaimer**:  
> MindBridge is a supportive, conversational first step toward professional mental health care.  
> **This tool does not diagnose mental health conditions, prescribe treatments, or replace a licensed clinical psychologist or psychiatrist.**

---

## 1. Project Overview & Purpose

MindBridge is designed to break down the barriers of stigma, uncertainty, and friction when individuals seek mental health support. When a user opens the application, they are greeted by an empathetic, supportive conversational environment where they can choose to interact via **typing** or **speaking**.

### Core Objectives:
1. **Low-Friction Conversational Assessment**: Facilitates gentle, empathetic self-reflection through structured screening inquiries grounded in established clinical psychometrics (PHQ-9 and GAD-7 themes).
2. **Immediate Crisis Triaging**: Actively detects markers of acute self-harm, suicidal intent, violence/harm to others, or abuse, instantly diverting users to localized emergency resources and crisis hotlines.
3. **Non-Diagnostic Distress Stratification**: Replaces clinical labels with clear, understandable support tiers:
   - **Low Distress**: Wellbeing support, psychoeducation, and self-care resources.
   - **Mild–Moderate Distress**: Recommendation to consult a licensed psychologist.
   - **High Distress**: Recommendation for urgent evaluation with a clinical psychologist or psychiatrist.
   - **Immediate Risk**: Priority crisis flow with immediate emergency contacts, safety planning, and human outreach encouragement.
4. **Ethically Verified Care Navigation**: Connects individuals to verified mental health professionals filtered by language, location, specialization, availability, and affordability.

---

## 2. Technical Requirements & Dataset Grounding

The 100 screening questions and conversational language patterns are grounded in validated clinical frameworks and reference datasets:
1. **BoltMonkey/psychology-question-answer (Hugging Face)**: Used to inform empathetic phrasing, non-judgmental conversational tone, and clinical vocabulary without using diagnostic labels.
2. **ALL IN Therapy Clinic (100 Therapy Questions)**: Used to formulate introspective, open-ended reflections on coping mechanisms, protective factors, and relational wellbeing.
3. **Validated Psychometric Questionnaires**:
   - **PHQ-9 (Patient Health Questionnaire-9)**: Scored 0–27 for depressive symptomatology across 9 standard items (interest, depressed mood, sleep, fatigue, appetite, self-worth, concentration, psychomotor changes, and thoughts of self-harm).
   - **GAD-7 (Generalized Anxiety Disorder-7)**: Scored 0–21 for generalized anxiety symptoms (nervousness, uncontrollable worry, excessive worry, trouble relaxing, restlessness, irritability, and impending dread).

### The 100 Structured Questions Taxonomy
Questions are categorized into 7 structured clinical domains in `screening_questions.json`:
- **Mood & Depressive Symptoms** (18 questions): Evaluates hedonic tone, energy, sadness, emotional balance.
- **Anxiety & Worry Symptoms** (16 questions): Evaluates somatic tension, cognitive worry, panic responses.
- **Stress & Coping** (14 questions): Evaluates burnout, perceived workload, emotional overwhelm, coping efficacy.
- **Sleep & Rest** (14 questions): Evaluates sleep onset, fragmentation, restorative quality, nightmare frequency.
- **Daily Functioning & Routine** (14 questions): Evaluates occupational performance, executive focus, social withdrawal.
- **Safety & Risk** (12 questions): Evaluates passive/active ideation, means access, prior attempts, abuse exposure.
- **Protective Factors & Hope** (12 questions): Evaluates social support, reasons for living, therapeutic openness, emotional anchors.

---

## 3. Scoring & Risk Detection Logic

### 3.1 Standard Psychometric Scoring
- **PHQ-9 Calculation**: Sum of 9 Likert items (0 to 3 scale):
  - `0–4`: Minimal depression symptoms
  - `5–9`: Mild depression symptoms
  - `10–14`: Moderate depression symptoms
  - `15–19`: Moderately severe depression symptoms
  - `20–27`: Severe depression symptoms
- **GAD-7 Calculation**: Sum of 7 Likert items (0 to 3 scale):
  - `0–4`: Minimal anxiety symptoms
  - `5–9`: Mild anxiety symptoms
  - `10–14`: Moderate anxiety symptoms
  - `15–21`: Severe anxiety symptoms

### 3.2 Overall Distress Index
Overall distress combines standard PHQ-9 and GAD-7 indices with supplemental sleep and functioning items:
$$\text{Distress Score} = \text{PHQ-9} + \text{GAD-7} + \sum (\text{Sleep \& Functioning Impairment Items})$$
- **Low**: Distress Score $< 10$ and no elevated subscales.
- **Moderate**: Distress Score $10 - 24$ or mild-to-moderate subscale elevations.
- **High**: Distress Score $\ge 25$ or severe scores on PHQ-9/GAD-7.

### 3.3 Safety & Crisis Gates
The safety engine implements deterministic overrides. If any critical gate is triggered:
1. **Suicide Intent / Plan**: Immediate transition to crisis state, regardless of numerical scores.
2. **Access to Lethal Means**: Escalation to emergency support.
3. **Harm to Others / Violence**: Transition to immediate safety and containment protocols.
4. **Active Domestic Abuse**: Direct referral to domestic violence crisis hotlines and safe shelters.

---

## 4. Multimodal Audio Architecture

### 4.1 Speech-to-Text & Transcription
- Powered by `gemini-3.5-transcribe` via the Google GenAI SDK.
- Supports raw PCM, WAV, and MP3 audio inputs.
- Configurable for **verbatim transcription** and **word-level timestamps** (`timestamp_granularities: ["word"]`) for speech cadence and pause evaluation.
- **Human-in-the-Loop Transcript Review**: Users are always presented with the transcribed text prior to analysis, allowing editing, redaction, or cancellation.

### 4.2 Text-to-Speech (TTS) & Humanized Voice Output
- Implemented with `gemini-3.1-flash-tts-preview` in `backend/gemini_tts.py`.
- Employs natural, warm acoustic personas (e.g., `Kore`, `Aoede`, `Puck`, `Fenrir`) to avoid cold, robotic speech.
- Supports **streaming audio synthesis** (`stream=True`) for low-latency voice agent interactions.
- Supports **multi-speaker generation** for psychoeducational dialogue roleplay between diverse voices.
- Converts 24kHz 16-bit mono raw PCM chunks into standard streaming WAV containers in memory without disk contention.

### 4.3 Calming Acoustic Support & Ethical Listening Rules
- **Explicit Consent**: Background soundscapes (binaural, nature, soft ambient) are off by default.
- **Volume Clamping**: Sound levels are capped at $<60\text{ dB}$ equivalent to prevent sensory overwhelm.
- **Microphone Coordination**: Background audio automatically pauses when the user speaks or records audio.
- **Crisis Silence**: Ambient music immediately stops whenever a crisis risk flag is raised to ensure cognitive clarity.
- **No Psychoacoustic Profiling**: Music preferences, listening duration, and volume settings are **never** used to infer psychiatric state or pathology.

---

## 5. Verified Professional Referral (India & Global)

MindBridge does not recommend unvetted directories or automated matching algorithms without statutory credential checks.

### Verification Standards in India:
- **Psychiatrists**: Verified through the **National Medical Commission (NMC)** registry (MBBS + MD/DNB in Psychiatry).
- **Clinical Psychologists**: Verified through the **Rehabilitation Council of India (RCI)** registry (holding an RCI-recognized M.Phil or Psy.D. in Clinical Psychology).
- **Filtering Dimensions**:
  - Languages spoken (Hindi, English, Bengali, Tamil, Telugu, Marathi, etc.)
  - Consultation mode (Online video vs. In-person clinic)
  - Clinical specialization (Trauma/PTSD, Adolescent Health, OCD, Mood Disorders)
  - Verified fee structures and sliding-scale accessibility options.

---

## 6. Safety, Privacy & Ethical Boundaries

| Principle | Implementation in MindBridge |
| :--- | :--- |
| **Non-Diagnostic Framing** | Never outputs DSM/ICD diagnosis strings (e.g., "Major Depressive Disorder"). Always outputs "Distress Level" and recommended support tiers. |
| **No "Brain Fixing" Claims** | Explicitly refrains from claiming to "cure," "re-wire," or "fix" cognitive neurological structures. |
| **Confidentiality & Consent** | Compliant with India's **Mental Healthcare Act, 2017 (Section 23)** and **Telemedicine Practice Guidelines (2020)**. |
| **Data Minimization** | Ephemeral voice processing; raw voice audio is not retained after transcription unless user opts into encrypted research logs. |
| **Audit Trails & Encryption** | Role-based database encryption, anonymized user session tokens, and auditable consent logs (`consent_logs`). |

---

## 7. Deliverables & File Layout

1. **`backend/screening_questions.json`**: Exactly 100 clinical screening questions across 7 domains with scoring rules and high-risk flags.
2. **`backend/clinical_screener.py`**: Python clinical screening engine implementing PHQ-9, GAD-7, distress indexing, crisis logic, and structured JSON reporting.
3. **`backend/gemini_tts.py`**: Gemini 3.1 TTS streaming, single-speaker, and multi-speaker synthesis.
4. **`backend/gemini_transcribe.py`**: Gemini 3.5 audio transcription with word-level timestamp integration.
5. **`demo_screener.py`**: Simulation script demonstrating clinical intake runs (moderate distress vs. acute crisis).
6. **`backend/server.py`**: Unified Flask server exposing `/api/screener/questions`, `/api/screener/evaluate`, `/api/voice/tts`, therapist directory, and chat endpoints.
