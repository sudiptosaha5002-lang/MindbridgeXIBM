# MindBridge Emotion Input Detection & Emotion Analysis Module

## System Architecture

The Emotional Input Detection Module acts as a continuous safety and empathetic monitoring layer. It sits between the User Interface and the conversational LLM. 
The module actively scans every incoming message (text or transcribed voice) and the recent conversation history to identify emotional states, risk factors, and the overall intensity of the user's input.

**Workflow:**
1. **User Input:** User speaks or types. If spoken, `VoiceboxPipeline` transcribes audio.
2. **Emotion Detection (Endpoint: `/api/detect-emotion`):** The module evaluates the text using a combination of multilingual lexical analysis, multi-turn context boosting, and clinical pattern matching.
3. **Interview Trigger:** If a moderate/high-intensity negative emotion is detected OR a clinical sensitivity flag is raised, the `needs_emotion_interview` flag is sent to the frontend.
4. **Emotion Interview Window:** The frontend displays an empathetic prompt ("I noticed you might be feeling..."). If accepted, it opens a dedicated multi-turn modal presenting targeted assessment questions in the user's preferred language (English, Bengali, or Hindi).
5. **Synthesis (Endpoint: `/api/analyze-emotions`):** Once all questions are answered, the module synthesizes the responses into a cohesive Emotional State Profile, mapping the dominant emotions, frequencies, and a final empathetic summary for the clinical engine.

## Supported Languages & Code-Mixing

The system natively supports English (`en`), Bengali (`bn`), and Hindi (`hi`), and seamlessly handles **code-mixed inputs** (e.g., Hinglish or Bengali-English mix). 

- **Detection Mechanism:** The system identifies code-mixing by evaluating character blocks (ASCII Latin characters vs. Brahmic/Indic unicode ranges). The module flags `is_code_mixed: true` when both are present, allowing the downstream LLM to respond in a similar natural code-mixed style.
- **Multilingual Lexicons:** Found in `backend/emotion_lexicons.json`. These include terms for 14 emotional categories, clinical sensitivity flags (e.g., suicidal ideation), and intensity modifiers across the three primary languages.

## Clinical Safety Protocols (Sensitivity Flags)

The module includes a strict clinical safety net (`risk_flag`), ensuring that users experiencing acute distress or suicidal thoughts are correctly categorized.

**Risk Flags:**
- **immediate:** Triggered by `suicidal_feelings` or `self_harm_thoughts`.
- **high:** Triggered by `intense_emotional_pain`.
- **moderate:** Triggered by `trauma_reference`.
- **none:** Default state.

*Disclaimer: MindBridge does not diagnose mental-health conditions. It is a supportive screening and care-navigation platform. In cases of "immediate" risk, the system is designed to route the user to emergency crisis resources.*

## Emotion Labels

The system tracks and scores the following emotional dimensions:
`sadness`, `hopelessness`, `anxiety`, `overwhelm`, `anger`, `fear`, `guilt`, `shame`, `loneliness`, `numbness`, `joy`, `calm`, `grief`, `emotional_exhaustion`.

## Simulated Models & Datasets

- **Lexicon Basis:** Simulated using extensive clinical NLP domain expertise, mapping culturally relevant expressions of distress in South Asian contexts (Bengali/Hindi) and Western contexts (English).
- **Audio/VAD:** The voice input system uses a `ScriptProcessorNode` for Voice Activity Detection (VAD) with a 4.5s silence threshold to ensure long, paused emotional thoughts are captured without premature cutoff.
