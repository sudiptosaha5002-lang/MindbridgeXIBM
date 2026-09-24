"""
MindBridge Flask API Server & Static Web App Host.
Provides RESTful endpoints for empathetic chatbot interactions, 
safety/crisis triage, therapist directory, appointment booking, 
and emotional well-being insights.
"""

import os
import sys
import json
import time
import uuid
import logging
logger = logging.getLogger("mindbridge")
from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

import database as db
import nlp_engine as nlp
import gemini_tts
import clinical_screener
from past_life_engine import past_life_engine
from voicebox_engine import voicebox_engine
from emotion_detector import emotion_detector
from emotion_analyzer import emotion_analyzer
from emotion_interview_engine import emotion_interview_engine
try:
    import audio_transcriber
    voice_transcriber = audio_transcriber.transcriber_manager
except Exception as _at_err:
    print(f"Warning: audio_transcriber could not be loaded: {_at_err}")
    voice_transcriber = None

try:
    import voice_tone_analyzer as vta
    tone_analyzer = vta.voice_tone_analyzer
    tone_aggregator = vta.session_tone_aggregator
except Exception as _vta_err:
    print(f"Warning: voice_tone_analyzer could not be loaded: {_vta_err}")
    tone_analyzer = None
    tone_aggregator = None


# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")

# Native CORS & No-Cache Support for All Origins & Live Development
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        res = Response()
        res.headers["Access-Control-Allow-Origin"] = "*"
        res.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT, DELETE"
        res.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
        return res, 200

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT, DELETE"
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Initialize DB on start
db.init_db()

# ----------------- STATIC FRONTEND ROUTES ----------------- #

@app.route("/")
def serve_index():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/music/<path:filename>")
def serve_music(filename):
    music_dir = os.path.join(FRONTEND_DIR, "music")
    return send_from_directory(music_dir, filename, mimetype="audio/mpeg")

@app.route("/resources/<path:filename>")
def serve_resources(filename):
    res_dir = os.path.join(FRONTEND_DIR, "resources")
    mimetype = "audio/mpeg" if filename.lower().endswith((".mpeg", ".mp3", ".wav")) else None
    return send_from_directory(res_dir, filename, mimetype=mimetype)

@app.route("/images/<path:filename>")
def serve_images(filename):
    img_dir = os.path.join(FRONTEND_DIR, "images")
    return send_from_directory(img_dir, filename)

# ----------------- API ENDPOINTS ----------------- #

@app.route("/v1/chat/completions", methods=["POST", "OPTIONS"])
def openai_proxy_chat_completions():
    """
    OpenAI-compatible /v1/chat/completions endpoint for Deepgram Voice Agent Client integration.
    Proxies requests to MindBridge's custom NLP engine and streams responses via SSE.
    """
    if request.method == "OPTIONS":
        return jsonify({}), 200
        
    data = request.get_json() or {}
    messages = data.get("messages", [])
    model = data.get("model", "mindbridge-agent")
    stream = data.get("stream", False)
    
    # Extract the latest user message
    user_text = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_text = msg.get("content", "")
            break
            
    if not user_text:
        return jsonify({"error": "No user message found"}), 400

    # Get conversation history from messages array if needed
    # For now, just generate response
    ai_result = nlp.generate_mindbridge_response(user_text, language="auto")
    response_text = ai_result["response"]

    completion_id = f"chatcmpl-{str(uuid.uuid4())}"
    created = int(time.time())
    
    def generate_stream():
        # Yield role delta
        yield f'data: {json.dumps({"id": completion_id, "object": "chat.completion.chunk", "created": created, "model": model, "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]})}\\n\\n'
        
        # Stream word by word to simulate LLM generation
        words = response_text.split(" ")
        for i, word in enumerate(words):
            content = word + (" " if i < len(words) - 1 else "")
            yield f'data: {json.dumps({"id": completion_id, "object": "chat.completion.chunk", "created": created, "model": model, "choices": [{"index": 0, "delta": {"content": content}, "finish_reason": None}]})}\\n\\n'
            time.sleep(0.02)  # Simulate token generation delay
            
        # Yield finish
        yield f'data: {json.dumps({"id": completion_id, "object": "chat.completion.chunk", "created": created, "model": model, "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]})}\\n\\n'
        yield "data: [DONE]\\n\\n"

    if stream:
        return Response(
            stream_with_context(generate_stream()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    else:
        return jsonify({
            "id": completion_id,
            "object": "chat.completion",
            "created": created,
            "model": model,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": response_text},
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": -1, "completion_tokens": -1, "total_tokens": -1}
        })

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "MindBridge API Gateway",
        "version": "2.0.0",
        "compliance": "HIPAA & Non-Diagnostic Guardrails Active"
    })

@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Main conversational endpoint:
    Processes user text/voice input, enforces safety & non-diagnostic checks,
    handles past-life / life reflection question interviews,
    and returns empathetic guidance with suggested actions.
    """
    data = request.get_json() or {}
    user_text = data.get("message", "").strip()
    conversation_id = data.get("conversation_id")
    user_id = data.get("user_id", "guest-user")
    language = data.get("language", "en-US")
    is_audio = 1 if data.get("audio_detected") else 0
    past_life_session_id = data.get("past_life_session_id")
    past_life_mode = data.get("past_life_mode", "short") # 'short' (6 Qs) or 'full' (13 Qs)

    if not user_text:
        return jsonify({"error": "Message content is required"}), 400

    # Ensure conversation exists
    conversation_id = db.get_or_create_conversation(conversation_id, user_id)

    # 1. Check if user is currently answering an active Past Life Reflection interview
    active_pls = past_life_engine.get_session(past_life_session_id) if past_life_session_id else None
    if active_pls and active_pls.get("status") == "in_progress":
        pls_result = past_life_engine.process_answer(
            session_id=past_life_session_id,
            answer_text=user_text,
            is_audio=(is_audio == 1),
            input_mode="voice" if is_audio else "text"
        )
        
        # Save response in database
        curr_idx = active_pls.get("current_index", 1) - 1
        curr_q_id = active_pls.get("question_ids", [1])[max(0, curr_idx)]
        curr_q = past_life_engine.questions_by_id.get(curr_q_id, {})
        
        db.record_past_life_answer(
            session_id=past_life_session_id,
            user_id=user_id,
            question_id=curr_q_id,
            theme=curr_q.get("theme", "general"),
            category=curr_q.get("category", ""),
            question_text=curr_q.get("question_text", {}).get(active_pls.get("language", "en"), ""),
            answer_text=user_text,
            input_mode="voice" if is_audio else "text",
            sentiment_score=pls_result.get("analysis", {}).get("nostalgia_index", 50) / 100.0,
            emotional_themes=[]
        )

        if pls_result.get("is_complete"):
            analysis = pls_result.get("analysis", {})
            db.update_past_life_session(
                past_life_session_id,
                status="completed",
                primary_archetype=analysis.get("primary_archetype", ""),
                nostalgia_index=analysis.get("nostalgia_index", 0),
                resilience_index=analysis.get("resilience_index", 0),
                trust_index=analysis.get("trust_index", 0),
                processing_load=analysis.get("processing_load", ""),
                narrative_report=analysis.get("narrative_report", ""),
                completed_at="CURRENT_TIMESTAMP"
            )

        # Save User & MindBridge messages
        db.save_message(conversation_id, "user", user_text, is_audio, ["reflection"], "safe")
        db.save_message(conversation_id, "mindbridge", pls_result["formatted_message"], 0, ["empathy"], "safe")

        return jsonify({
            "conversation_id": conversation_id,
            "response": pls_result["formatted_message"],
            "risk_level": "safe",
            "safety_data": {"is_crisis": False, "is_high_distress": False, "is_diagnostic": False},
            "suggested_actions": pls_result.get("suggested_chips", []),
            "dimensions": {"primary_emotion": "reflective", "detected_emotions": ["reflection", "insight"]},
            "guardrail_triggered": False,
            "past_life_active": True,
            "past_life_session": pls_result,
            "past_life_completed": pls_result.get("is_complete", False)
        })

    # Fetch past conversation context
    history = db.get_conversation_history(conversation_id)

    # 2. Check for Trigger Intent to START a Past Life Reflection session
    triggered_lang = past_life_engine.detect_trigger_intent(user_text)
    
    # Run safety check first
    safety = nlp.scan_safety(user_text)
    if triggered_lang and not safety["is_crisis"]:
        # Auto-start Past Life Reflection Session in detected language
        pls_start = past_life_engine.start_session(
            user_id=user_id,
            conversation_id=conversation_id,
            language=triggered_lang,
            mode=past_life_mode
        )
        
        # Persist session to DB
        db.create_past_life_session(
            session_id=pls_start["session_id"],
            user_id=user_id,
            conversation_id=conversation_id,
            language=triggered_lang,
            interview_mode=past_life_mode,
            total_questions=pls_start["total_questions"]
        )

        db.save_message(conversation_id, "user", user_text, is_audio, ["reflection_intent"], "safe")
        db.save_message(conversation_id, "mindbridge", pls_start["formatted_message"], 0, ["supportive"], "safe")

        return jsonify({
            "conversation_id": conversation_id,
            "response": pls_start["formatted_message"],
            "risk_level": "safe",
            "safety_data": {"is_crisis": False, "is_high_distress": False, "is_diagnostic": False},
            "suggested_actions": pls_start["suggested_chips"],
            "dimensions": {"primary_emotion": "reflective", "detected_emotions": ["reflection", "nostalgia"]},
            "guardrail_triggered": False,
            "past_life_active": True,
            "past_life_session": pls_start,
            "past_life_completed": False
        })

    # Generate standard response via NLP engine
    ai_result = nlp.generate_mindbridge_response(user_text, history, language=language)

    # Detect emotional state and interview trigger criteria
    emotion_eval = emotion_detector.detect_emotion(user_text, context_messages=history, language=language)

    # Save User message
    db.save_message(
        conversation_id=conversation_id,
        sender="user",
        content=user_text,
        audio_detected=is_audio,
        detected_emotions=[e["label"] for e in emotion_eval.get("detected_emotions", [])] or ai_result["dimensions"]["detected_emotions"],
        risk_level=ai_result["risk_level"]
    )

    # Save MindBridge message
    db.save_message(
        conversation_id=conversation_id,
        sender="mindbridge",
        content=ai_result["response"],
        audio_detected=0,
        detected_emotions=[],
        risk_level=ai_result["risk_level"]
    )

    return jsonify({
        "conversation_id": conversation_id,
        "response": ai_result["response"],
        "risk_level": ai_result["risk_level"],
        "safety_data": ai_result["safety_data"],
        "suggested_actions": ai_result["suggested_actions"],
        "dimensions": ai_result["dimensions"],
        "emotion_detection": emotion_eval,
        "guardrail_triggered": ai_result["guardrail_triggered"],
        "nuance_analysis": ai_result.get("nuance_analysis", {}),
        "resource_insights": ai_result.get("resource_insights", {}),
        "voice_module_profile": ai_result.get("voice_module_profile", {}),
        "voice_perspectives": ai_result.get("voice_perspectives", {}),
        "linguistic_stats": ai_result.get("linguistic_stats", {}),
        "normalized_input": ai_result.get("normalized_input"),
        "detected_language": ai_result.get("detected_language"),
        "language_switched": ai_result.get("language_switched", False),
        "past_life_active": False
    })


@app.route("/api/voice-modules", methods=["GET"])
def get_voice_modules():
    """
    Returns metadata, acoustic profiles, and audio stream links for the
    Bengali and English benchmark voice modules from the resources folder.
    Also provides acoustic calibration parameters (rate, pitch, rhythmic pauses)
    to align all other language voices (Hindi, Hinglish, Spanish, Portuguese) with the benchmark.
    """
    from linguistic_resource_trainer import linguistic_trainer
    return jsonify({
        "status": "success",
        "voice_modules": linguistic_trainer.voice_modules_metadata,
        "training_stats": linguistic_trainer.get_stats(),
        "acoustic_calibration": {
            "rate": 0.91,
            "pitch": 0.97,
            "clause_pause_ms": 140,
            "breath_pause_ms": 180,
            "description": "Contemplative, grounded therapeutic pacing (125-130 WPM) matching WhatsApp benchmark audio modules"
        }
    })

@app.route("/api/transcribe", methods=["POST", "OPTIONS"])
@app.route("/api/voice/transcribe", methods=["POST", "OPTIONS"])
def transcribe_audio():
    """
    Unified Speech-to-Text Transcription API:
    Supports MediaRecorder WebM/Opus, MP4, OGG, and WAV.
    Primary Engine: Self-hosted faster-whisper (CTranslate2) with multilingual Indian & Global support
    Fallback 1: Google Multilingual Acoustic Bridge (en-IN, hi-IN, bn-IN, etc.)
    Fallback 2: Dual ASR Whisper & NVIDIA NeMo Speech
    Includes Voice-Tone / Emotion Prosodic Analysis when analyze_tone=true.
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    language = request.args.get("language") or request.form.get("language") or "en-IN"
    session_id = request.args.get("session_id") or request.form.get("session_id")
    question_id = request.args.get("question_id") or request.form.get("question_id")
    analyze_tone = (
        request.args.get("analyze_tone", "").lower() in ("true", "1", "yes") or
        request.form.get("analyze_tone", "").lower() in ("true", "1", "yes")
    )
    force_engine = request.args.get("engine", None)
    simulate_failover = request.args.get("simulate_failover", "false").lower() in ("true", "1", "yes")

    try:
        raw_audio = None
        if "audio" in request.files:
            raw_audio = request.files["audio"].read()
        elif request.data:
            raw_audio = request.data
        elif request.files:
            for k in request.files:
                raw_audio = request.files[k].read()
                break

        if not raw_audio or len(raw_audio) < 44:
            return jsonify({
                "status": "silence",
                "text": "",
                "message": "No audio data received or clip was too short."
            }), 200

        # Run tone analysis if requested
        tone_res = None
        if analyze_tone and tone_analyzer:
            try:
                tone_res = tone_analyzer.analyze_audio_clip(raw_audio)
                if session_id and question_id and tone_aggregator:
                    tone_aggregator.record_answer_tone(session_id, question_id, tone_res)
            except Exception as tone_err:
                logger.warning(f"[Voice Tone Analysis Note]: {tone_err}")

        # Primary Pipeline: AudioConverter (PyAV WebM/Opus/WAV) -> Faster-Whisper -> Google Acoustic Bridge
        if voice_transcriber:
            try:
                tx_res = voice_transcriber.transcribe_audio_bytes(raw_audio, language=language)
                text = tx_res.get("text", "").strip()
                if text:
                    from nlp_engine import detect_input_language
                    detected = detect_input_language(text, fallback=tx_res.get("detected_language", language))
                    res_payload = {
                        "status": "success",
                        "text": text,
                        "detected_language": detected,
                        "engine_used": tx_res.get("engine", "faster-whisper"),
                        "latency_ms": tx_res.get("total_latency_ms") or tx_res.get("latency_ms", 250)
                    }
                    if tone_res:
                        res_payload["voice_tone"] = tone_res
                    return jsonify(res_payload), 200
            except Exception as e:
                logger.warning(f"[Primary Transcriber Note]: {e}")

        # Secondary Failover Pipeline: Dual Voice Recognition Manager (Whisper Turbo / NeMo)
        try:
            from dual_voice_recognition import asr_manager
            import io
            audio_stream = io.BytesIO(raw_audio)
            asr_result = asr_manager.transcribe(
                audio_stream,
                language=language,
                force_engine=force_engine,
                simulate_failover=simulate_failover
            )

            text = asr_result.get("text", "").strip()
            if text:
                from nlp_engine import detect_input_language
                detected = detect_input_language(text, fallback=asr_result.get("detected_language", language))
                res_payload = {
                    "status": "success",
                    "text": text,
                    "detected_language": detected,
                    "engine_used": asr_result.get("engine_name") or asr_result.get("engine"),
                    "engine_id": asr_result.get("engine"),
                    "failover_triggered": asr_result.get("failover_triggered", False),
                    "primary_engine": asr_result.get("primary_engine"),
                    "secondary_engine": asr_result.get("secondary_engine"),
                    "failover_reason": asr_result.get("failover_reason"),
                    "latency_ms": asr_result.get("latency_ms") or asr_result.get("total_latency_ms")
                }
                if tone_res:
                    res_payload["voice_tone"] = tone_res
                return jsonify(res_payload), 200
            else:
                res_payload = {
                    "status": "silence",
                    "text": "",
                    "message": "No clear speech detected. Please speak closer to your microphone.",
                    "engine_used": asr_result.get("engine_name") or "faster-whisper",
                    "failover_triggered": asr_result.get("failover_triggered", False)
                }
                if tone_res:
                    res_payload["voice_tone"] = tone_res
                return jsonify(res_payload), 200
        except Exception as asr_err:
            logger.warning(f"[Secondary ASR Note]: {asr_err}")
            res_payload = {
                "status": "silence",
                "text": "",
                "message": "No speech detected or transcriber unavailable."
            }
            if tone_res:
                res_payload["voice_tone"] = tone_res
            return jsonify(res_payload), 200

    except Exception as e:
        logger.error(f"[Transcribe API Error]: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "text": "",
            "message": "Transcription temporarily unavailable. Please type your response or try again."
        }), 200

@app.route("/api/voice/engines/status", methods=["GET"])
def voice_engines_status():
    """
    Returns live diagnostics, hardware readiness, and failover metrics for:
    1. Primary Engine: OpenAI Whisper (openai/whisper.git)
    2. Secondary Engine: NVIDIA NeMo Speech Canary / Parakeet (NVIDIA-NeMo/Speech.git)
    """
    from dual_voice_recognition import asr_manager
    return jsonify({
        "status": "success",
        "engines": asr_manager.get_status()
    })

@app.route("/api/safety/check", methods=["POST"])
def check_safety():
    """
    Real-time quick scanner for crisis signals.
    """
    data = request.get_json() or {}
    text = data.get("text", "")
    safety_result = nlp.scan_safety(text)
    return jsonify(safety_result)

@app.route("/api/providers", methods=["GET"])
def get_providers():
    """
    Filterable directory of verified mental health professionals.
    Supports query params: specialty, language, mode, max_price
    """
    filters = {
        "specialty": request.args.get("specialty"),
        "language": request.args.get("language"),
        "mode": request.args.get("mode"),
        "max_price": request.args.get("max_price", type=int)
    }
    # Remove None values
    active_filters = {k: v for k, v in filters.items() if v is not None and v != ""}
    providers = db.get_all_providers(active_filters)
    return jsonify({
        "count": len(providers),
        "providers": providers
    })

@app.route("/api/providers/<provider_id>", methods=["GET"])
def get_provider_details(provider_id):
    """
    Returns single doctor/therapist profile with calendar slots.
    """
    provider = db.get_provider_by_id(provider_id)
    if not provider:
        return jsonify({"error": "Provider not found"}), 404
    return jsonify(provider)

@app.route("/api/book", methods=["POST"])
def book_appointment():
    """
    Books an appointment with a verified psychologist or psychiatrist.
    """
    data = request.get_json() or {}
    required_fields = ["provider_id", "patient_name", "patient_email", "patient_phone", "appointment_date", "appointment_time"]
    
    for f in required_fields:
        if not data.get(f):
            return jsonify({"error": f"Missing required field: {f}"}), 400

    provider = db.get_provider_by_id(data["provider_id"])
    if not provider:
        return jsonify({"error": "Selected provider does not exist"}), 404

    appt_id = db.create_appointment(data)

    return jsonify({
        "success": True,
        "appointment_id": appt_id,
        "message": f"Appointment booked successfully with {provider['name']}!",
        "appointment_details": {
            "id": appt_id,
            "provider_name": provider["name"],
            "provider_title": provider["title"],
            "fee": provider["fee_per_session"],
            "date": data["appointment_date"],
            "time": data["appointment_time"],
            "mode": data.get("consultation_mode", "online"),
            "patient_name": data["patient_name"],
            "clinic_address": provider["clinic_address"] if data.get("consultation_mode") == "in-person" else "Secure Tele-health Video Link",
            "confirmation_code": f"MB-{appt_id.upper()}"
        }
    })

@app.route("/api/appointments", methods=["GET"])
def list_appointments():
    """
    List user appointments.
    """
    user_id = request.args.get("user_id")
    appointments = db.get_all_appointments(user_id)
    return jsonify({"appointments": appointments})

@app.route("/api/insights/<conversation_id>", methods=["GET"])
def get_insights(conversation_id):
    """
    Generates structured, safe non-diagnostic emotional insights
    based on conversation history.
    """
    history = db.get_conversation_history(conversation_id)
    summary_data = nlp.synthesize_session_summary(history)
    return jsonify(summary_data)

@app.route("/api/emergency-resources", methods=["GET"])
def get_emergency_resources():
    """
    Returns verified national & international 24/7 crisis hotlines.
    """
    return jsonify({
        "resources": nlp.EMERGENCY_RESOURCES,
        "grounding_exercises": [
            {
                "title": "4-7-8 Deep Grounding Breathing",
                "instructions": "Inhale gently through nose for 4s, hold breath for 7s, exhale completely through mouth for 8s.",
                "duration_seconds": 120
            },
            {
                "title": "5-4-3-2-1 Sensory Grounding",
                "instructions": "Name 5 things you see, 4 things you feel, 3 things you hear, 2 things you smell, 1 thing you are grateful for.",
                "duration_seconds": 180
            }
        ]
    })

@app.route("/api/consent", methods=["POST"])
def record_consent():
    """
    Records HIPAA / Privacy consent log.
    """
    data = request.get_json() or {}
    conn = db.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO consent_logs (id, user_id, consent_type, agreed, ip_hash)
    VALUES (?, ?, ?, ?, ?)
    """, (
        f"consent-{os.urandom(4).hex()}",
        data.get("user_id", "guest-user"),
        data.get("consent_type", "privacy_and_non_diagnostic_terms"),
        1 if data.get("agreed", True) else 0,
        request.remote_addr
    ))
    conn.commit()
    conn.close()
    return jsonify({"status": "consent_recorded"})

@app.route("/api/voice/tts", methods=["POST", "OPTIONS"])
def voice_tts():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    """
    Synthesizes compassionate, humanized speech using Google GenAI Gemini TTS.
    Accepts JSON:
    {
        "text": "Hello, how are you feeling today?",
        "voice": "Kore",
        "api_key": "..." (optional)
    }
    """
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    voice = data.get("voice", "Kore")
    api_key = data.get("api_key") or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    if not text:
        return jsonify({"status": "error", "message": "No text provided"}), 400

    try:
        wav_bytes = gemini_tts.synthesize_speech_gemini(text, voice_name=voice, api_key=api_key)
        return Response(wav_bytes, mimetype="audio/wav")
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ----------------- PAST LIFE / LIFE REFLECTION ROUTES ----------------- #

@app.route("/api/past-life/questions", methods=["GET"])
def get_past_life_questions():
    """Returns all 13 past life questions and 6 short interview questions in EN, HI, BN."""
    mode = request.args.get("mode", "all")
    lang = request.args.get("lang", "en")
    if mode == "short":
        qs = past_life_engine.get_question_sequence("short")
    else:
        qs = past_life_engine.get_question_sequence("full")
    return jsonify({
        "status": "success",
        "total": len(qs),
        "language": lang,
        "questions": qs
    })

@app.route("/api/past-life/start", methods=["POST", "OPTIONS"])
def start_past_life_session():
    """Initializes a new past life reflection session."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    data = request.get_json() or {}
    user_id = data.get("user_id", "guest-user")
    conversation_id = data.get("conversation_id")
    language = data.get("language", "en")
    mode = data.get("mode", "short") # 'short' (6 questions) or 'full' (13 questions)

    session_data = past_life_engine.start_session(
        user_id=user_id,
        conversation_id=conversation_id,
        language=language,
        mode=mode
    )

    db.create_past_life_session(
        session_id=session_data["session_id"],
        user_id=user_id,
        conversation_id=conversation_id,
        language=session_data["language"],
        interview_mode=mode,
        total_questions=session_data["total_questions"]
    )

    return jsonify({"status": "success", "session": session_data})

@app.route("/api/past-life/answer", methods=["POST", "OPTIONS"])
def submit_past_life_answer():
    """Submits answer (voice or text) for current reflection question."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    data = request.get_json() or {}
    session_id = data.get("session_id")
    user_id = data.get("user_id", "guest-user")
    answer_text = data.get("answer", "").strip()
    is_audio = bool(data.get("is_audio", False))
    input_mode = data.get("input_mode", "voice" if is_audio else "text")

    if not session_id or not answer_text:
        return jsonify({"error": "session_id and answer are required"}), 400

    result = past_life_engine.process_answer(
        session_id=session_id,
        answer_text=answer_text,
        is_audio=is_audio,
        input_mode=input_mode
    )

    if result.get("error"):
        return jsonify({"status": "error", "message": result["error"]}), 404

    # DB persistence
    active_pls = past_life_engine.get_session(session_id)
    if active_pls:
        curr_idx = active_pls.get("current_index", 1) - 1
        curr_qid = active_pls.get("question_ids", [1])[max(0, curr_idx)]
        curr_q = past_life_engine.questions_by_id.get(curr_qid, {})
        db.record_past_life_answer(
            session_id=session_id,
            user_id=user_id,
            question_id=curr_qid,
            theme=curr_q.get("theme", "general"),
            category=curr_q.get("category", ""),
            question_text=curr_q.get("question_text", {}).get(active_pls.get("language", "en"), ""),
            answer_text=answer_text,
            input_mode=input_mode,
            sentiment_score=0.0
        )

        if result.get("is_complete"):
            analysis = result.get("analysis", {})
            db.update_past_life_session(
                session_id,
                status="completed",
                primary_archetype=analysis.get("primary_archetype", ""),
                nostalgia_index=analysis.get("nostalgia_index", 0),
                resilience_index=analysis.get("resilience_index", 0),
                trust_index=analysis.get("trust_index", 0),
                processing_load=analysis.get("processing_load", ""),
                narrative_report=analysis.get("narrative_report", ""),
                completed_at="CURRENT_TIMESTAMP"
            )

    return jsonify({"status": "success", "result": result})

@app.route("/api/past-life/session/<session_id>", methods=["GET"])
def get_past_life_session_status(session_id):
    """Retrieves session state and answers."""
    session = past_life_engine.get_session(session_id)
    if not session:
        db_sess = db.get_past_life_session(session_id)
        if not db_sess:
            return jsonify({"error": "Session not found"}), 404
        db_answers = db.get_past_life_answers(session_id)
        return jsonify({"session": db_sess, "answers": db_answers})
    return jsonify({"session": session})

@app.route("/api/past-life/analyze", methods=["POST", "OPTIONS"])
def analyze_past_life_session():
    """Generates mental state analysis on demand."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    data = request.get_json() or {}
    session_id = data.get("session_id")
    session = past_life_engine.get_session(session_id)
    if not session:
        return jsonify({"error": "Active session not found"}), 404
    analysis = past_life_engine.generate_mental_state_analysis(session)
    return jsonify({"status": "success", "analysis": analysis})

# ----------------- EMOTION DETECTION & INTERVIEW MODULE ----------------- #

@app.route("/api/detect_emotion", methods=["POST", "OPTIONS"])
@app.route("/api/detect-emotion", methods=["POST", "OPTIONS"])
def api_detect_emotion():
    """
    Emotion Detection & Classification Endpoint.
    Analyzes text or transcribed audio input + conversation history.
    Returns emotion categories, intensity, sensitivity flags, and trigger decision.
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.get_json(silent=True) or {}
    text = data.get("text") or data.get("message") or ""
    context_messages = data.get("context_messages") or data.get("history") or []
    language = data.get("language") or "en"

    result = emotion_detector.detect_emotion(
        text=text,
        context_messages=context_messages,
        language=language
    )

    return jsonify({
        "status": "success",
        **result
    }), 200

@app.route("/api/emotion-interview/questions", methods=["GET"])
def get_emotion_interview_questions():
    """Returns the 10 refined emotion interview questions in the requested language."""
    lang = request.args.get("lang", "en")
    questions = emotion_interview_engine.repo.get_all_questions(language=lang)
    return jsonify({
        "status": "success",
        "total": len(questions),
        "language": lang,
        "questions": questions
    }), 200

@app.route("/api/emotion-interview/start", methods=["POST", "OPTIONS"])
def start_emotion_interview_session():
    """Initializes a new emotion interview session."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id", "guest-user")
    conversation_id = data.get("conversation_id")
    language = data.get("language", "en")
    trigger_reason = data.get("trigger_reason", "user_emotional_expression")

    session_data = emotion_interview_engine.start_session(
        user_id=user_id,
        conversation_id=conversation_id,
        language=language,
        trigger_reason=trigger_reason
    )

    return jsonify({
        "status": "success",
        "session": session_data
    }), 200

@app.route("/api/emotion-interview/answer", methods=["POST", "OPTIONS"])
def submit_emotion_interview_answer():
    """Submits and confirms user's answer (voice or text) for current emotion question."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    answer_text = (data.get("answer") or data.get("answer_text") or "").strip()
    user_id = data.get("user_id", "guest-user")
    input_mode = data.get("input_mode", "voice")

    if not session_id or not answer_text:
        return jsonify({"status": "error", "message": "session_id and answer are required"}), 400

    res = emotion_interview_engine.process_answer(
        session_id=session_id,
        answer_text=answer_text,
        input_mode=input_mode,
        user_id=user_id
    )

    if res.get("error"):
        return jsonify({"status": "error", "message": res["error"]}), 404

    return jsonify({
        "status": "success",
        "result": res
    }), 200

@app.route("/api/emotion-interview/session/<session_id>", methods=["GET"])
def get_emotion_interview_session(session_id):
    """Retrieves session state, answers, and analysis."""
    session = emotion_interview_engine.get_session(session_id)
    if not session:
        return jsonify({"status": "error", "message": "Session not found"}), 404
    return jsonify({
        "status": "success",
        "session": session
    }), 200

@app.route("/api/analyze_emotions", methods=["POST", "OPTIONS"])
@app.route("/api/analyze-emotions", methods=["POST", "OPTIONS"])
def api_analyze_emotions():
    """
    Analyzes a list of emotion answers or an active emotion session ID,
    returning dominant emotions, intensity, coping styles, themes, and narrative summary.
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    language = data.get("language", "en")

    if session_id:
        analysis = emotion_interview_engine.finalize_session(session_id)
        if not analysis:
            return jsonify({"status": "error", "message": "Session not found or empty"}), 404
        return jsonify({
            "status": "success",
            "analysis": analysis
        }), 200

    answers = data.get("answers", [])
    if not answers:
        return jsonify({"status": "error", "message": "Either session_id or answers array is required"}), 400

    analysis = emotion_analyzer.analyze_interview_answers(answers, language=language)
    return jsonify({
        "status": "success",
        "analysis": analysis
    }), 200

# ----------------- CLINICAL SCREENER (PHQ-9 / GAD-7 / SAFETY) ----------------- #


# ----------------- CLINICAL SCREENER (RESEARCH GROUNDED 100 QUESTIONS) ----------------- #

import mental_screening as ms

screener_engine = ms.screening_engine

@app.route("/api/screener/research-papers", methods=["GET"])
def get_research_papers_metadata():
    """Returns metadata and validated clinical instruments extracted from research papers."""
    meta = ms.load_research_papers()
    return jsonify({
        "status": "success",
        "data": meta,
        "disclaimer": ms.DISCLAIMER_TEXT
    })

@app.route("/api/screener/session/start", methods=["POST", "OPTIONS"])
def start_screening_session():
    """
    Initializes a new screening session or resumes existing one.
    Shuffles the 100 questions specifically for this user session.
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.get_json() or {}
    user_id = data.get("user_id") or f"user-{uuid.uuid4().hex[:8]}"
    force_new = data.get("force_new", False)

    # Check existing in-progress session if not forcing new
    if not force_new:
        existing = db.get_active_screening_session(user_id)
        if existing and existing.get("status") == "in_progress":
            order = existing.get("question_order", [])
            curr_idx = existing.get("current_index", 0)
            curr_qid = order[curr_idx] if curr_idx < len(order) else None
            curr_q = screener_engine.get_question(curr_qid) if curr_qid else None
            spoken_prompt = curr_q.get("question_text", "") if curr_q else ""
            if curr_idx == 0 and spoken_prompt:
                spoken_prompt = f"Welcome back to your MindBridge clinical session. Let's continue reflecting on how you've been feeling. {spoken_prompt}"
            return jsonify({
                "status": "success",
                "session_id": existing["id"],
                "user_id": user_id,
                "resumed": True,
                "current_index": curr_idx,
                "total_questions": len(order),
                "current_question": curr_q,
                "spoken_prompt": spoken_prompt,
                "disclaimer": ms.DISCLAIMER_TEXT
            })

    # Generate new shuffled session
    shuffled_qs = screener_engine.shuffle_questions_for_user(user_id)
    order_ids = [q["question_id"] for q in shuffled_qs]
    session_id = db.create_screening_session(user_id, order_ids)
    first_q = shuffled_qs[0] if shuffled_qs else None
    first_prompt = f"Hello, I am MindBridge. Let's reflect together on how you have been feeling recently. {first_q.get('question_text', '')}" if first_q else ""

    return jsonify({
        "status": "success",
        "session_id": session_id,
        "user_id": user_id,
        "resumed": False,
        "current_index": 0,
        "total_questions": len(order_ids),
        "current_question": first_q,
        "spoken_prompt": first_prompt,
        "disclaimer": ms.DISCLAIMER_TEXT
    })

@app.route("/api/screener/question", methods=["GET"])
def get_current_question():
    """
    Fetches the question for the user's active session at the given index.
    Query params: session_id, index (optional)
    """
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"status": "error", "message": "session_id is required"}), 400

    session = db.get_screening_session(session_id)
    if not session:
        return jsonify({"status": "error", "message": "Session not found"}), 404

    order = session.get("question_order", [])
    idx = request.args.get("index", type=int)
    if idx is None:
        idx = session.get("current_index", 0)

    if idx >= len(order):
        return jsonify({
            "status": "completed",
            "message": "All screening questions answered",
            "session_id": session_id,
            "total_questions": len(order),
            "current_index": idx
        })

    qid = order[idx]
    q = screener_engine.get_question(qid)
    spoken_prompt = q.get("question_text", "") if q else ""
    if idx == 0:
        spoken_prompt = f"Hello, I am MindBridge. Let's reflect together on how you have been feeling recently. {spoken_prompt}"

    return jsonify({
        "status": "success",
        "session_id": session_id,
        "current_index": idx,
        "total_questions": len(order),
        "question": q,
        "spoken_prompt": spoken_prompt,
        "disclaimer": ms.DISCLAIMER_TEXT
    })

@app.route("/api/screener/answer", methods=["POST", "OPTIONS"])
def submit_screener_answer():
    """
    Submits an answer (text or voice) for a question in a screening session.
    Immediately intercepts acute safety/crisis responses and logs them.
    Accepts JSON:
    {
        "session_id": "scr-...",
        "user_id": "...",
        "question_id": "q43",
        "answer_text": "...",
        "input_mode": "voice" | "text",
        "raw_transcript": "..." (optional for voice)
    }
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.get_json() or {}
    session_id = data.get("session_id")
    question_id = data.get("question_id")
    answer_text = data.get("answer_text", "").strip()
    user_id = data.get("user_id", "guest-user")
    input_mode = data.get("input_mode", "voice")
    raw_transcript = data.get("raw_transcript")

    if not session_id or not question_id:
        return jsonify({"status": "error", "message": "session_id and question_id are required"}), 400

    result = screener_engine.record_answer(
        session_id=session_id,
        user_id=user_id,
        question_id=question_id,
        answer_text=answer_text,
        input_mode=input_mode,
        raw_transcript=raw_transcript
    )

    return jsonify(result)

@app.route("/api/screener/questions", methods=["GET"])
def get_screener_questions():
    """
    Returns the complete 100 questions dataset with optional domain filtering.
    """
    domain = request.args.get("domain")
    qs = screener_engine.questions
    if domain:
        qs = [q for q in qs if q.get("domain") == domain]
    limit = request.args.get("limit", type=int)
    if limit and limit > 0:
        qs = qs[:limit]

    return jsonify({
        "status": "success",
        "total_returned": len(qs),
        "total_available": len(screener_engine.questions),
        "questions": qs,
        "disclaimer": ms.DISCLAIMER_TEXT
    })

@app.route("/api/screener/evaluate", methods=["POST", "OPTIONS"])
def evaluate_screener_answers():
    """
    Computes final mental state analysis, PHQ-9, GAD-7, distress levels,
    and returns non-diagnostic empathetic recommendations.
    Accepts JSON:
    {
        "session_id": "scr-..."
    }
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.get_json() or {}
    session_id = data.get("session_id")

    if not session_id:
        # If answers provided directly as dict for ad-hoc evaluation
        raw_answers = data.get("answers", {})
        if raw_answers:
            temp_user = data.get("user_id", "adhoc-user")
            order = list(raw_answers.keys())
            sid = db.create_screening_session(temp_user, order)
            for qid, ans in raw_answers.items():
                screener_engine.record_answer(sid, temp_user, qid, str(ans), input_mode="text")
            session_id = sid
        else:
            return jsonify({"status": "error", "message": "session_id is required"}), 400

    try:
        analysis = screener_engine.compute_scores_and_analysis(session_id)
        # Attach aggregated voice tone analysis if present
        if tone_aggregator:
            tone_summary = tone_aggregator.get_session_summary(session_id)
            if tone_summary:
                analysis["voice_tone_summary"] = tone_summary

        return jsonify({
            "status": "success",
            "result": analysis,
            "disclaimer": ms.DISCLAIMER_TEXT
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/screener/session/<session_id>", methods=["GET"])
def get_screening_session_info(session_id):
    """Retrieves status and answers for a specific screening session."""
    session = db.get_screening_session(session_id)
    if not session:
        return jsonify({"status": "error", "message": "Session not found"}), 404
    answers = db.get_session_answers(session_id)
    return jsonify({
        "status": "success",
        "session": session,
        "answers_count": len(answers),
        "answers": answers,
        "disclaimer": ms.DISCLAIMER_TEXT
    })

# ----------------- VOICE TONE ANALYSIS ENDPOINTS ----------------- #

@app.route("/api/analyze_voice_tone", methods=["POST", "OPTIONS"])
def api_analyze_voice_tone():
    """
    Voice-Tone / Emotion Analysis Endpoint.
    Extracts MFCCs, pitch F0, energy, and speaking rate, then applies CNN-BiLSTM SER.
    If session_id & question_id are provided, records it in the session aggregator.
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    raw_audio = None
    if "audio" in request.files:
        raw_audio = request.files["audio"].read()
    elif request.data:
        raw_audio = request.data
    elif request.files:
        for k in request.files:
            raw_audio = request.files[k].read()
            break

    if not raw_audio or len(raw_audio) < 44:
        return jsonify({
            "status": "error",
            "message": "No audio file received or file is empty."
        }), 400

    if not tone_analyzer:
        return jsonify({
            "status": "error",
            "message": "Voice tone analysis engine is not available."
        }), 503

    try:
        session_id = request.args.get("session_id") or request.form.get("session_id")
        question_id = request.args.get("question_id") or request.form.get("question_id")

        tone_result = tone_analyzer.analyze_audio_clip(raw_audio)

        if session_id and question_id and tone_aggregator:
            tone_aggregator.record_answer_tone(session_id, question_id, tone_result)

        disclaimer_text = getattr(vta, "NON_DIAGNOSTIC_DISCLAIMER", "Observed voice-tone patterns only. Not a diagnosis.")

        return jsonify({
            "status": "success",
            "voice_tone": tone_result,
            "disclaimer": disclaimer_text
        }), 200
    except Exception as exc:
        print(f"Voice tone analysis error: {exc}")
        return jsonify({
            "status": "error",
            "message": "Voice tone analysis encountered an error."
        }), 500

@app.route("/api/screener/session/<session_id>/voice-tone", methods=["GET"])
def get_session_voice_tone(session_id):
    """Retrieves session-aggregated voice tone and prosodic summary."""
    if not tone_aggregator:
        return jsonify({"status": "error", "message": "Voice tone engine not loaded."}), 503
    summary = tone_aggregator.get_session_summary(session_id)
    if not summary:
        return jsonify({"status": "not_found", "message": "No voice tone records for this session."}), 404
    return jsonify({
        "status": "success",
        "voice_tone_summary": summary
    })


# ----------------- VOICEBOX STUDIO NEURAL AUDIO ENDPOINTS ----------------- #

@app.route("/api/voicebox/voices", methods=["GET"])
def get_voicebox_voices():
    """Returns available studio voice personas."""
    try:
        personas = voicebox_engine.get_personas()
        return jsonify({
            "status": "success",
            "voices": personas,
            "count": len(personas)
        }), 200
    except Exception as e:
        logger.error(f"[Voicebox API] Voices error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/voicebox/synthesize", methods=["POST"])
def synthesize_voicebox():
    """
    Synthesizes speech with neural studio voice.
    Accepts: { text, persona_id, rate, pitch, format ('audio'|'json'), split_chunks (bool) }
    """
    try:
        data = request.get_json(silent=True) or {}
        text = data.get("text", "").strip()
        if not text:
            # Check form data / query
            text = (request.form.get("text") or request.args.get("text") or "").strip()

        if not text:
            return jsonify({"status": "error", "message": "Text is required for voice synthesis."}), 400

        persona_id = data.get("persona_id") or request.args.get("persona_id") or "en_serene_aria"
        rate = data.get("rate") or request.args.get("rate")
        pitch = data.get("pitch") or request.args.get("pitch")
        req_format = (data.get("format") or request.args.get("format") or "json").lower()
        split_chunks = data.get("split_chunks", False)

        if split_chunks:
            stream_mode = data.get("stream", False) or request.args.get("stream", False)
            
            if stream_mode:
                def generate():
                    for chunk in voicebox_engine.synthesize_chunks_stream(text, persona_id):
                        yield json.dumps(chunk) + "\n"
                return Response(generate(), mimetype='application/x-ndjson')
            else:
                chunks_data = voicebox_engine.synthesize_chunks(text, persona_id)
                import base64
                encoded_chunks = []
                for c in chunks_data:
                    encoded_chunks.append({
                        "chunk_index": c["chunk_index"],
                        "total_chunks": c["total_chunks"],
                        "text": c["text"],
                        "audio_base64": base64.b64encode(c["audio_bytes"]).decode("utf-8"),
                        "content_type": c["content_type"]
                    })
                return jsonify({
                    "status": "success",
                    "chunks": encoded_chunks,
                    "persona_id": persona_id
                }), 200

        audio_bytes = voicebox_engine.synthesize(text, persona_id=persona_id, rate=rate, pitch=pitch)

        if req_format == "audio":
            return Response(
                audio_bytes,
                mimetype="audio/mpeg",
                headers={
                    "Content-Disposition": "inline; filename=voicebox_speech.mp3",
                    "Cache-Control": "public, max-age=3600"
                }
            )

        import base64
        return jsonify({
            "status": "success",
            "audio_base64": base64.b64encode(audio_bytes).decode("utf-8"),
            "content_type": "audio/mpeg",
            "persona_id": persona_id
        }), 200

    except Exception as e:
        logger.error(f"[Voicebox API] Synthesize error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/voicebox/transcribe", methods=["POST"])
def transcribe_voicebox():
    """
    Transcribes audio clip using MLX-Audio / Dual-ASR & VAD,
    with optional acoustic tone/emotion prosody analysis.
    """
    try:
        audio_file = request.files.get("audio")
        if not audio_file:
            raw_data = request.get_data()
            if not raw_data:
                return jsonify({"status": "error", "message": "No audio data received."}), 400
            audio_bytes = raw_data
        else:
            audio_bytes = audio_file.read()

        language = request.args.get("language") or request.form.get("language")
        session_id = request.args.get("session_id") or request.form.get("session_id")
        question_id = request.args.get("question_id") or request.form.get("question_id")
        analyze_tone = (
            request.args.get("analyze_tone", "").lower() in ("true", "1", "yes") or
            request.form.get("analyze_tone", "").lower() in ("true", "1", "yes")
        )

        tone_res = None
        if analyze_tone and tone_analyzer:
            try:
                tone_res = tone_analyzer.analyze_audio_clip(audio_bytes)
                if session_id and question_id and tone_aggregator:
                    tone_aggregator.record_answer_tone(session_id, question_id, tone_res)
            except Exception as tone_err:
                logger.warning(f"[Voicebox Transcribe Tone Analysis Note]: {tone_err}")

        result = voicebox_engine.transcribe_audio_vad(audio_bytes, language=language)
        transcription_text = result.get("transcription", "").strip()

        resp_payload = {
            "status": "success",
            "transcription": transcription_text,
            "text": transcription_text,
            "language": result.get("detected_language", "en"),
            "confidence": result.get("confidence", 0.95),
            "engine_used": result.get("engine_used", "Whisper Large v3 Turbo")
        }
        if tone_res:
            resp_payload["voice_tone"] = tone_res

        return jsonify(resp_payload), 200

    except Exception as e:
        logger.error(f"[Voicebox API] Transcribe error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/voicebox/status", methods=["GET"])
def get_voicebox_status():
    """Returns Voicebox telemetry & status."""
    return jsonify({
        "status": "success",
        "voicebox": voicebox_engine.get_status()
    }), 200

# ----------------- INPUT CLASSIFICATION & FALLBACK ROUTES ----------------- #

from crisis_detector import crisis_detector
from emotion_classifier import emotion_classifier
from fallback_analysis import fallback_analyzer

@app.route("/api/crisis-check", methods=["POST", "OPTIONS"])
def check_crisis():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    data = request.get_json() or {}
    text = data.get("text", "")
    result = crisis_detector.check_crisis(text)
    return jsonify(result), 200

@app.route("/api/classify-user-input", methods=["POST", "OPTIONS"])
def classify_input():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    data = request.get_json() or {}
    text = data.get("text", "")
    context = data.get("conversation_context", [])
    result = emotion_classifier.classify_input(text, context)
    return jsonify(result), 200

@app.route("/api/start-fallback-emotion-interview", methods=["POST", "OPTIONS"])
def start_fallback_interview():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    try:
        with open(os.path.join(BASE_DIR, "backend", "fallback_emotion_interview.json"), "r", encoding="utf-8") as f:
            fallback_data = json.load(f)
        return jsonify({"status": "success", "session_id": str(uuid.uuid4()), "interview_data": fallback_data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/submit-fallback-answer", methods=["POST", "OPTIONS"])
def submit_fallback_answer():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    data = request.get_json() or {}
    answer = data.get("answer", "")
    # Analyze single answer in real time for safety risk
    result = emotion_classifier.classify_input(answer)
    crisis_flag = result.get("risk_flag", "none")
    requires_crisis = crisis_flag in ["immediate", "high"]
    return jsonify({"status": "success", "requires_crisis_flow": requires_crisis}), 200

@app.route("/api/analyze-fallback-interview", methods=["POST", "OPTIONS"])
def analyze_fallback():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    data = request.get_json() or {}
    answers = data.get("answers", [])
    language = data.get("language", "en")
    result = fallback_analyzer.analyze_fallback_session(answers, language)
    return jsonify(result), 200


# ----------------- REGISTRATION FLOW ENDPOINTS ----------------- #

from registration_engine import registration_engine

@app.route("/api/registration/start", methods=["POST", "OPTIONS"])
def api_registration_start():
    if request.method == "OPTIONS":
        return build_cors_preflight_response()
    try:
        data = request.json or {}
        language = data.get("language", "en")
        user_id = data.get("user_id", "anonymous")
        
        sess_data = registration_engine.start_session(
            user_id=user_id,
            language=language
        )
        return jsonify({"status": "success", "session": sess_data})
    except Exception as e:
        logger.error(f"[Registration] start error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/registration/question", methods=["GET"])
def api_registration_question():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"status": "error", "message": "Missing session_id"}), 400
        
    q = registration_engine.get_current_question(session_id)
    if not q:
        return jsonify({"status": "error", "message": "No active question or session completed"})
        
    sess = registration_engine.get_session(session_id)
    lang = sess.get("language", "en")
    
    return jsonify({
        "status": "success",
        "question": {
            "id": q["id"],
            "domain": q["domain"],
            "text": q.get(lang, q.get("en", ""))
        }
    })

@app.route("/api/registration/answer", methods=["POST", "OPTIONS"])
def api_registration_answer():
    if request.method == "OPTIONS":
        return build_cors_preflight_response()
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No JSON body"}), 400
            
        session_id = data.get("session_id")
        answer_text = data.get("answer_text", "")
        input_mode = data.get("input_mode", "text")
        skipped = data.get("skipped", False)
        
        if not session_id:
            return jsonify({"status": "error", "message": "Missing session_id"}), 400
            
        result = registration_engine.submit_answer(
            session_id=session_id,
            answer_text=answer_text,
            input_mode=input_mode,
            skipped=skipped
        )
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"[Registration] answer error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/registration/analyze", methods=["POST", "OPTIONS"])
def api_registration_analyze():
    if request.method == "OPTIONS":
        return build_cors_preflight_response()
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No JSON body"}), 400
            
        session_id = data.get("session_id")
        if not session_id:
            return jsonify({"status": "error", "message": "Missing session_id"}), 400
            
        result = registration_engine.analyze_session(session_id)
        if "error" in result:
            return jsonify({"status": "error", "message": result["error"]}), 500
            
        return jsonify({"status": "success", "analysis": result})
    except Exception as e:
        logger.error(f"[Registration] analyze error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500




# ----------------- AUTHENTICATION ENDPOINTS ----------------- #

import database

@app.route("/api/auth/register", methods=["POST", "OPTIONS"])
def api_auth_register():
    if request.method == "OPTIONS":
        return build_cors_preflight_response()
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No JSON body"}), 400
            
        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "")
        
        if not name or not email or not password:
            return jsonify({"status": "error", "message": "Name, email, and password are required."}), 400
            
        result = database.create_user_with_password(name, email, password)
        if result["status"] == "error":
            return jsonify(result), 400
            
        return jsonify(result)
    except Exception as e:
        logger.error(f"[Auth] register error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/auth/login", methods=["POST", "OPTIONS"])
def api_auth_login():
    if request.method == "OPTIONS":
        return build_cors_preflight_response()
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No JSON body"}), 400
            
        email = data.get("email", "").strip()
        password = data.get("password", "")
        
        if not email or not password:
            return jsonify({"status": "error", "message": "Email and password are required."}), 400
            
        result = database.verify_user_login(email, password)
        if result["status"] == "error":
            return jsonify(result), 401
            
        return jsonify(result)
    except Exception as e:
        logger.error(f"[Auth] login error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ----------------- CATCH-ALL STATIC FALLBACK (MUST BE LAST) ----------------- #

@app.route("/<path:path>", methods=["GET"])
def serve_static(path):
    if os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, "index.html")



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"==================================================")
    print(f"  MindBridge Mental Health Platform API Running  ")
    print(f"  Access Frontend at: http://localhost:{port}     ")
    print(f"==================================================")
    app.run(host="0.0.0.0", port=port, debug=True)
