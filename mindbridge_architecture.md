# MindBridge: Comprehensive Project Description and Architecture

## 1. Project Overview
**MindBridge** is an advanced, multilingual mental health platform and conversational AI (chatbot) designed to provide empathetic emotional support, mental state screening, and crisis intervention. It is built to serve as a supportive companion, offering non-diagnostic therapeutic insights, active listening, and guidance to verified mental health professionals.

The platform is inherently safe, prioritizing immediate crisis detection, adhering to ethical guardrails (strictly avoiding medical diagnoses), and seamlessly supporting multiple languages (English, Hindi, Hinglish, Bengali, Spanish, Portuguese) with cultural nuances.

---

## 2. Core Features
1. **Multilingual Empathy & Dynamic Language Switching:**
   - Supports English, Hindi (Devanagari & Romanized/Hinglish), Bengali (Bangla & Banglish), Spanish, and Portuguese.
   - Automatically detects the user's language and mid-conversation switches to align the chatbot's responses and voice output.
2. **Real-time Crisis & Safety Intervention:**
   - Always-on rule-based and LLM-backed crisis detection.
   - Immediately halts normal screening if self-harm or suicidal intent is detected, providing localized emergency hotline numbers (e.g., Tele-MANAS, Vandrevala Foundation, 988) and safe grounding exercises.
3. **Non-Diagnostic Ethical Guardrails:**
   - Strictly deflects clinical diagnostic queries (e.g., "Do I have depression?").
   - Clearly communicates its role as an emotional companion and refuses to prescribe medications or provide medical diagnoses.
4. **Dynamic Emotion Classification & Voice Analysis:**
   - Detects primary and secondary emotions, emotional intensity, and psychological dimensions (stressors, sleep patterns, mood).
   - Voice companion module with synthesized empathetic responses tailored to the detected emotional state.
5. **Interactive Assessments & Reflection Modules:**
   - "Past Life Reflection" sessions for deep introspective interviewing.
   - "Mental State Analyzer" with dynamically generated, emotionally-aware questions to understand the user's psychological landscape.
6. **Professional Support Routing:**
   - Recommends and links users to verified mental health professionals (Psychiatrists, Clinical Psychologists) based on the detected emotional profile and distress level.

---

## 3. Technology Stack (Main)
- **Backend Framework:** Python with Flask (RESTful API architecture).
- **Database:** SQLite (development) with PostgreSQL compatibility (production).
- **Frontend Framework:** Vanilla JavaScript, HTML5, and CSS3 (custom CSS for a highly dynamic, calming UI with glassmorphism and smooth animations).
- **NLP & Generative AI:** Google Gemini 1.5 Flash (via `google.generativeai`) for deep semantic understanding and emotion classification.
- **Audio Processing:** Custom voice tone analysis, Speech-to-Text (STT), and Text-to-Speech (TTS) integration.

---

## 4. Full Project Architecture
The project follows a decoupled Client-Server architecture.

### A. Frontend Layer (`frontend/`)
- **`app.js`**: The central state manager and UI controller. Handles real-time API communication, voice recording, dynamic UI updates (e.g., emotion chips, language selection), and interactive modals.
- **`styles.css` / `calm-welcome.css`**: Provides a premium, therapeutic UI/UX, prioritizing psychological safety through color psychology, smooth transitions, and responsive design.
- **`voicebox.js`**: Handles audio capturing and TTS integration for the Voice Companion.

### B. API Layer (`backend/server.py`)
- The Flask server acts as the entry point for all frontend requests.
- **Endpoints include:** 
  - `/api/chat`: Processes user messages and returns AI responses.
  - `/api/classify-user-input`: Intercepts and categorizes intent.
  - `/api/registration/start`: Initiates structured emotional screening.
- Handles session state, conversation history logging, and database transactions (`database.py`).

### C. NLP & Cognitive Engine Layer
This is the core brain of MindBridge, consisting of multiple specialized modules:
- **`nlp_engine.py`**: The central orchestration script for text processing. Handles language detection, integrates safety checks, and synthesizes the final response.
- **`emotion_classifier.py`**: Uses Gemini LLM to classify user input into emotional categories and recommend next actions.
- **`crisis_detector.py`**: A deterministic regex and pattern-matching engine that acts as the absolute first line of defense against severe mental health crises.
- **`emotion_analyzer.py` / `dynamic_mental_state_analyzer.py`**: Extracts semantic nuances, sleep indicators, coping styles, and contextual stressors from the user's dialogue.

---

## 5. NLP Model Working Procedure (Step-by-Step)
When a user sends a message, it undergoes a strict pipeline to guarantee safety, empathy, and accuracy.

1. **Input Reception & Normalization:**
   - The user's text (or transcribed audio) is received.
   - If the input is in a specific regional dialect (e.g., colloquial Bengali), the `linguistic_resource_trainer.py` normalizes it for accurate processing.

2. **Absolute Safety & Crisis Check (Pre-LLM):**
   - The `crisis_detector.py` scans the raw input against a multi-lingual list of high-severity triggers (e.g., *suicide, self-harm, "no reason to live"*).
   - **If triggered:** The NLP pipeline halts immediately. A hardcoded, culturally localized emergency response is dispatched, overriding the LLM to prevent any unpredictable or unsafe AI output.

3. **Dynamic Language Detection:**
   - `detect_input_language` in `nlp_engine.py` analyzes script (Indic vs. Latin) and token morphology.
   - Uses an English Dominance metric (TF/IDF-like stopword matching) to prevent false-positive Hinglish classifications, securely routing the text to the correct localized language module (en-US, hi-IN, bn-IN, es-ES, pt-BR).

4. **Deep Semantic Classification (LLM Integration):**
   - The text is passed to `emotion_classifier.py` which queries the Gemini 1.5 Flash model.
   - A heavily constrained System Prompt instructs the LLM to output a strict JSON containing:
     - `input_category` (e.g., *anxiety_stress_input*, *sadness_grief_input*).
     - `detected_emotions`, `emotion_intensity`, and `time_scope`.
     - `risk_flag` (as a secondary safety net).
     - `next_action` (e.g., *offer_emotion_interview*, *continue_normal_flow*).

5. **Non-Diagnostic Guardrail Filtering:**
   - Before drafting the response, the system checks for diagnostic intent (e.g., "Do I have ADHD?").
   - If found, a deflection protocol is activated, empathetically explaining the chatbot's limitations and suggesting a verified human professional.

6. **Empathetic Response Synthesis:**
   - If safe, the NLP engine synthesizes the final response by combining:
     - **Contextual Mirroring**: Reflecting the user's feelings to validate them.
     - **Therapeutic Insights**: Drawing from `resource_knowledge_engine.py` based on psychological best practices (e.g., WHO PM+).
     - **Actionable Coping Strategies**: Suggesting grounded, practical next steps (e.g., "4-7-8 breathing").
   - The response is strictly enforced to be in the exact same language detected in Step 3.

7. **Voice Calibration (Optional):**
   - If audio output is requested, the text is sent to the TTS engine. The acoustic profile (pitch, pace, pauses) is dynamically calibrated based on the detected emotional intensity (e.g., slower and lower pitch for "grief" or "overwhelmed" states).
