"""
Database management module for MindBridge.
Implements SQLite storage with PostgreSQL-compatible schema for users, 
conversations, messages, verified mental health providers, appointments, and consent.
"""

import sqlite3
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "mindbridge.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT DEFAULT 'Anonymous User',
        email TEXT UNIQUE,
        password_hash TEXT,
        phone TEXT,
        preferred_language TEXT DEFAULT 'en',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Consent Logs Table (HIPAA / Privacy Compliance)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT;")
    except sqlite3.OperationalError:
        pass # Column might already exist

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS consent_logs (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        consent_type TEXT,
        agreed INTEGER DEFAULT 1,
        ip_hash TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Conversations Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        title TEXT DEFAULT 'Emotional Check-in',
        overall_sentiment TEXT,
        stress_level INTEGER DEFAULT 50,
        mood_label TEXT DEFAULT 'Reflective',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Messages Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        conversation_id TEXT,
        sender TEXT, -- 'user' or 'mindbridge'
        content TEXT,
        audio_detected INTEGER DEFAULT 0,
        detected_emotions TEXT,
        risk_level TEXT DEFAULT 'safe', -- 'safe', 'moderate', 'emergency'
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conversation_id) REFERENCES conversations (id)
    )
    """)

    # Mood Entries Table (For Longitudinal Well-being Insights)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mood_entries (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        conversation_id TEXT,
        mood_score INTEGER, -- 1 to 10
        energy_score INTEGER, -- 1 to 10
        sleep_hours REAL,
        stress_category TEXT,
        notes TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Verified Providers Table (Psychologists & Psychiatrists)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS providers (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        title TEXT NOT NULL, -- e.g., 'Clinical Psychologist', 'Consultant Psychiatrist'
        qualification TEXT NOT NULL, -- e.g., 'M.Phil (Clinical Psychology), RCI Registered'
        experience_years INTEGER NOT NULL,
        specializations TEXT NOT NULL, -- JSON array
        languages TEXT NOT NULL, -- JSON array
        location_city TEXT NOT NULL,
        consultation_modes TEXT NOT NULL, -- JSON array: ['online', 'in-person']
        clinic_address TEXT,
        fee_per_session INTEGER NOT NULL, -- in INR
        rating REAL DEFAULT 4.9,
        reviews_count INTEGER DEFAULT 84,
        avatar_url TEXT,
        bio TEXT,
        is_verified INTEGER DEFAULT 1,
        available_days TEXT NOT NULL, -- JSON array
        available_slots TEXT NOT NULL -- JSON array
    )
    """)

    # Appointments Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id TEXT PRIMARY KEY,
        provider_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        patient_name TEXT NOT NULL,
        patient_email TEXT NOT NULL,
        patient_phone TEXT NOT NULL,
        appointment_date TEXT NOT NULL,
        appointment_time TEXT NOT NULL,
        consultation_mode TEXT NOT NULL, -- 'online' or 'in-person'
        concerns_summary TEXT,
        status TEXT DEFAULT 'confirmed', -- 'confirmed', 'completed', 'cancelled'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (provider_id) REFERENCES providers (id)
    )
    """)

    # Screening Sessions Table (100-Question Mental Health Screening)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS screening_sessions (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        status TEXT DEFAULT 'in_progress', -- 'in_progress', 'completed', 'crisis_halted'
        question_order TEXT NOT NULL, -- JSON array of question_ids in shuffled order
        current_index INTEGER DEFAULT 0,
        phq9_score INTEGER,
        phq9_severity TEXT,
        gad7_score INTEGER,
        gad7_severity TEXT,
        stress_score INTEGER,
        sleep_score INTEGER,
        functioning_score INTEGER,
        overall_distress TEXT,
        risk_flag TEXT DEFAULT 'none',
        summary_text TEXT,
        recommended_action TEXT,
        crisis_flag INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP
    )
    """)

    # Screening Answers Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS screening_answers (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        question_id TEXT NOT NULL,
        answer_text TEXT NOT NULL,
        numeric_score REAL,
        input_mode TEXT DEFAULT 'voice', -- 'voice' or 'text'
        raw_transcript TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES screening_sessions (id)
    )
    """)

    # Past Life & Life Reflection Sessions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS past_life_sessions (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        conversation_id TEXT,
        language TEXT DEFAULT 'en',
        interview_mode TEXT DEFAULT 'short', -- 'short' (6 Qs) or 'full' (13 Qs)
        status TEXT DEFAULT 'in_progress', -- 'in_progress', 'completed', 'paused'
        current_index INTEGER DEFAULT 0,
        total_questions INTEGER DEFAULT 6,
        primary_archetype TEXT,
        nostalgia_index INTEGER,
        resilience_index INTEGER,
        trust_index INTEGER,
        processing_load TEXT,
        narrative_report TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP
    )
    """)

    # Past Life Reflection Answers Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS past_life_answers (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        question_id INTEGER NOT NULL,
        theme TEXT,
        category TEXT,
        question_text TEXT NOT NULL,
        answer_text TEXT NOT NULL,
        input_mode TEXT DEFAULT 'text', -- 'voice' or 'text'
        sentiment_score REAL DEFAULT 0.0,
        emotional_themes TEXT, -- JSON array
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES past_life_sessions (id)
    )
    """)

    # Emotion Interview Sessions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS emotion_interview_sessions (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        conversation_id TEXT,
        language TEXT DEFAULT 'en',
        trigger_reason TEXT,
        status TEXT DEFAULT 'in_progress', -- 'in_progress', 'completed', 'declined'
        current_index INTEGER DEFAULT 0,
        total_questions INTEGER DEFAULT 10,
        dominant_emotions TEXT, -- JSON array
        overall_intensity TEXT,
        coping_style TEXT,
        themes_identified TEXT, -- JSON array
        narrative_summary TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP
    )
    """)

    # Emotion Interview Answers Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS emotion_interview_answers (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        question_id INTEGER NOT NULL,
        theme TEXT,
        question_text TEXT NOT NULL,
        answer_text TEXT NOT NULL,
        input_mode TEXT DEFAULT 'voice', -- 'voice' or 'text'
        detected_emotions TEXT, -- JSON array
        intensity TEXT,
        sensitivity_flags TEXT, -- JSON array
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES emotion_interview_sessions (id)
    )
    """)

    conn.commit()
    seed_providers(cursor)
    conn.commit()
    conn.close()


def seed_providers(cursor):
    """Seed initial verified psychologists and psychiatrists"""
    cursor.execute("SELECT COUNT(*) as count FROM providers")
    if cursor.fetchone()['count'] > 0:
        return

    sample_providers = [
        {
            "id": "prov-1",
            "name": "Dr. Ananya Sharma",
            "title": "Senior Clinical Psychologist",
            "qualification": "Ph.D. in Clinical Psychology (NIMHANS), RCI Reg.",
            "experience_years": 11,
            "specializations": json.dumps(["Anxiety & Panic", "Depression", "Workplace Stress & Burnout", "Sleep Disorders"]),
            "languages": json.dumps(["English", "Hindi"]),
            "location_city": "New Delhi / National (Online)",
            "consultation_modes": json.dumps(["online", "in-person"]),
            "clinic_address": "MindCare Wellness Hub, Vasant Vihar, New Delhi",
            "fee_per_session": 1800,
            "rating": 4.95,
            "reviews_count": 142,
            "avatar_url": "https://images.unsplash.com/photo-1594824813593-138382d56a34?w=400&auto=format&fit=crop&q=80",
            "bio": "Dr. Ananya Sharma specializes in Cognitive Behavioral Therapy (CBT) and Mindfulness-Based Stress Reduction (MBSR). She provides a warm, non-judgmental atmosphere to explore persistent worry, career fatigue, and emotional overwhelm.",
            "available_days": json.dumps(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]),
            "available_slots": json.dumps(["10:00 AM", "11:30 AM", "03:00 PM", "05:00 PM", "06:30 PM"])
        },
        {
            "id": "prov-2",
            "name": "Dr. Rajesh K. Varma",
            "title": "Consultant Neuro-Psychiatrist",
            "qualification": "MBBS, MD (Psychiatry - AIIMS), Dip. Psych.",
            "experience_years": 16,
            "specializations": json.dumps(["Mood Disorders", "Severe Anxiety & OCD", "ADHD & Focus", "Sleep & Insomnia"]),
            "languages": json.dumps(["English", "Hindi", "Bengali"]),
            "location_city": "Kolkata / Online Pan-India",
            "consultation_modes": json.dumps(["online", "in-person"]),
            "clinic_address": "Serenity Neuro-Psychiatry Centre, Salt Lake Sector 1, Kolkata",
            "fee_per_session": 2200,
            "rating": 4.92,
            "reviews_count": 210,
            "avatar_url": "https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=400&auto=format&fit=crop&q=80",
            "bio": "Dr. Rajesh Varma combines psychiatric medical evaluation with holistic lifestyle interventions. Known for his compassionate approach in managing chronic emotional distress and neuro-chemical imbalances.",
            "available_days": json.dumps(["Tuesday", "Wednesday", "Thursday", "Saturday", "Sunday"]),
            "available_slots": json.dumps(["11:00 AM", "01:00 PM", "04:30 PM", "06:00 PM", "07:30 PM"])
        },
        {
            "id": "prov-3",
            "name": "Meera Sen, M.Phil",
            "title": "Counseling Psychologist & Psychotherapist",
            "qualification": "M.Phil Psychology (TISS Mumbai), Certified ACT Practitioner",
            "experience_years": 8,
            "specializations": json.dumps(["Relationship & Family", "Self-Esteem & Identity", "Trauma Recovery", "Student & Young Adult Well-being"]),
            "languages": json.dumps(["English", "Hindi", "Marathi"]),
            "location_city": "Mumbai / Online Pan-India",
            "consultation_modes": json.dumps(["online"]),
            "clinic_address": "Virtual Care Studio, Bandra West, Mumbai",
            "fee_per_session": 1500,
            "rating": 4.88,
            "reviews_count": 98,
            "avatar_url": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=400&auto=format&fit=crop&q=80",
            "bio": "Meera works with young adults and professionals navigating life transitions, impostor syndrome, and relational conflicts through Acceptance & Commitment Therapy (ACT) and person-centered dialog.",
            "available_days": json.dumps(["Monday", "Wednesday", "Friday", "Saturday"]),
            "available_slots": json.dumps(["09:30 AM", "12:00 PM", "02:30 PM", "04:00 PM", "07:00 PM"])
        },
        {
            "id": "prov-4",
            "name": "Dr. Karthik Sundaram",
            "title": "Psychiatrist & Behavioral Health Specialist",
            "qualification": "MBBS, DNB (Psychiatry), Member of IPS",
            "experience_years": 12,
            "specializations": json.dumps(["Stress Management", "Depressive States", "Grief & Loss", "Bipolar Support"]),
            "languages": json.dumps(["English", "Tamil", "Hindi"]),
            "location_city": "Bengaluru / Online Pan-India",
            "consultation_modes": json.dumps(["online", "in-person"]),
            "clinic_address": "Aura Behavioral Health Clinic, Indiranagar, Bengaluru",
            "fee_per_session": 2000,
            "rating": 4.96,
            "reviews_count": 165,
            "avatar_url": "https://images.unsplash.com/photo-1537368910025-700350fe46c7?w=400&auto=format&fit=crop&q=80",
            "bio": "Dr. Karthik focuses on de-stigmatizing psychiatric care and creating personalized recovery roadmaps that empower clients to regain vitality, restorative sleep, and emotional equilibrium.",
            "available_days": json.dumps(["Monday", "Tuesday", "Thursday", "Friday", "Sunday"]),
            "available_slots": json.dumps(["10:30 AM", "01:30 PM", "03:30 PM", "05:30 PM", "08:00 PM"])
        },
        {
            "id": "prov-5",
            "name": "Priyanka Roy, M.Sc",
            "title": "Cognitive Behavioral & Mindfulness Therapist",
            "qualification": "M.Sc in Applied Psychology, Certified Mindfulness Coach (Oxford MBCT)",
            "experience_years": 7,
            "specializations": json.dumps(["Daily Stress & Overwhelm", "Social Anxiety", "Habit Reformation", "Mindfulness"]),
            "languages": json.dumps(["English", "Hindi", "Bengali"]),
            "location_city": "Online Pan-India",
            "consultation_modes": json.dumps(["online"]),
            "clinic_address": "Tele-Therapy Suite, Kolkata",
            "fee_per_session": 1200,
            "rating": 4.91,
            "reviews_count": 87,
            "avatar_url": "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=400&auto=format&fit=crop&q=80",
            "bio": "Priyanka blends classical CBT with practical mindfulness exercises, helping individuals untangle cognitive distortions and build daily resilience against everyday pressures.",
            "is_verified": 1,
            "available_days": json.dumps(["Tuesday", "Thursday", "Friday", "Saturday", "Sunday"]),
            "available_slots": json.dumps(["11:00 AM", "02:00 PM", "04:00 PM", "06:00 PM"])
        }
    ]

    for p in sample_providers:
        cursor.execute("""
        INSERT INTO providers (
            id, name, title, qualification, experience_years, specializations,
            languages, location_city, consultation_modes, clinic_address,
            fee_per_session, rating, reviews_count, avatar_url, bio, is_verified,
            available_days, available_slots
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p["id"], p["name"], p["title"], p["qualification"], p["experience_years"],
            p["specializations"], p["languages"], p["location_city"],
            p["consultation_modes"], p["clinic_address"], p["fee_per_session"],
            p["rating"], p["reviews_count"], p["avatar_url"], p["bio"],
            p.get("is_verified", 1), p["available_days"], p["available_slots"]
        ))

# Provider Query Helpers
def get_all_providers(filters=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM providers WHERE is_verified = 1"
    params = []

    if filters:
        if filters.get("specialty"):
            query += " AND specializations LIKE ?"
            params.append(f"%{filters['specialty']}%")
        if filters.get("language"):
            query += " AND languages LIKE ?"
            params.append(f"%{filters['language']}%")
        if filters.get("mode"):
            query += " AND consultation_modes LIKE ?"
            params.append(f"%{filters['mode']}%")
        if filters.get("max_price"):
            query += " AND fee_per_session <= ?"
            params.append(filters["max_price"])

    query += " ORDER BY rating DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    results = []
    for r in rows:
        item = dict(r)
        item["specializations"] = json.loads(item["specializations"])
        item["languages"] = json.loads(item["languages"])
        item["consultation_modes"] = json.loads(item["consultation_modes"])
        item["available_days"] = json.loads(item["available_days"])
        item["available_slots"] = json.loads(item["available_slots"])
        results.append(item)

    conn.close()
    return results

def get_provider_by_id(provider_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM providers WHERE id = ?", (provider_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    item = dict(row)
    item["specializations"] = json.loads(item["specializations"])
    item["languages"] = json.loads(item["languages"])
    item["consultation_modes"] = json.loads(item["consultation_modes"])
    item["available_days"] = json.loads(item["available_days"])
    item["available_slots"] = json.loads(item["available_slots"])
    return item

# Booking Helper
def create_appointment(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    appt_id = f"appt-{uuid.uuid4().hex[:8]}"
    cursor.execute("""
    INSERT INTO appointments (
        id, provider_id, user_id, patient_name, patient_email,
        patient_phone, appointment_date, appointment_time,
        consultation_mode, concerns_summary, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'confirmed')
    """, (
        appt_id,
        data.get("provider_id"),
        data.get("user_id", "guest-user"),
        data.get("patient_name"),
        data.get("patient_email"),
        data.get("patient_phone"),
        data.get("appointment_date"),
        data.get("appointment_time"),
        data.get("consultation_mode", "online"),
        data.get("concerns_summary", "")
    ))
    conn.commit()
    conn.close()
    return appt_id

def get_all_appointments(user_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute("""
        SELECT a.*, p.name as provider_name, p.title as provider_title, p.avatar_url as provider_avatar
        FROM appointments a
        JOIN providers p ON a.provider_id = p.id
        WHERE a.user_id = ?
        ORDER BY a.created_at DESC
        """, (user_id,))
    else:
        cursor.execute("""
        SELECT a.*, p.name as provider_name, p.title as provider_title, p.avatar_url as provider_avatar
        FROM appointments a
        JOIN providers p ON a.provider_id = p.id
        ORDER BY a.created_at DESC
        """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Conversation & Message Helpers
def save_message(conversation_id, sender, content, audio_detected=0, detected_emotions=None, risk_level="safe"):
    conn = get_db_connection()
    cursor = conn.cursor()
    msg_id = f"msg-{uuid.uuid4().hex[:8]}"
    cursor.execute("""
    INSERT INTO messages (id, conversation_id, sender, content, audio_detected, detected_emotions, risk_level)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        msg_id,
        conversation_id,
        sender,
        content,
        audio_detected,
        json.dumps(detected_emotions or []),
        risk_level
    ))
    cursor.execute("""
    UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?
    """, (conversation_id,))
    conn.commit()
    conn.close()
    return msg_id

def get_conversation_history(conversation_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC
    """, (conversation_id,))
    rows = cursor.fetchall()
    conn.close()
    results = []
    for r in rows:
        item = dict(r)
        item["detected_emotions"] = json.loads(item["detected_emotions"] or "[]")
        results.append(item)
    return results

def get_or_create_conversation(conv_id=None, user_id="guest-user"):
    conn = get_db_connection()
    cursor = conn.cursor()
    if not conv_id:
        conv_id = f"conv-{uuid.uuid4().hex[:8]}"
        cursor.execute("""
        INSERT INTO conversations (id, user_id) VALUES (?, ?)
        """, (conv_id, user_id))
        conn.commit()
    else:
        cursor.execute("SELECT id FROM conversations WHERE id = ?", (conv_id,))
        if not cursor.fetchone():
            cursor.execute("""
            INSERT INTO conversations (id, user_id) VALUES (?, ?)
            """, (conv_id, user_id))
            conn.commit()
    conn.close()
    return conv_id

# ----------------- SCREENING REPOSITORY HELPERS ----------------- #

def create_screening_session(user_id, question_order):
    """Creates a new screening session with randomized question order."""
    session_id = f"scr-{uuid.uuid4().hex[:10]}"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO screening_sessions (id, user_id, status, question_order, current_index)
    VALUES (?, ?, 'in_progress', ?, 0)
    """, (session_id, user_id, json.dumps(question_order)))
    conn.commit()
    conn.close()
    return session_id

def get_screening_session(session_id):
    """Fetches screening session by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM screening_sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    data = dict(row)
    data["question_order"] = json.loads(data["question_order"] or "[]")
    return data

def get_active_screening_session(user_id):
    """Retrieves current in-progress screening session for a user if exists."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM screening_sessions 
    WHERE user_id = ? AND status = 'in_progress'
    ORDER BY created_at DESC LIMIT 1
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    data = dict(row)
    data["question_order"] = json.loads(data["question_order"] or "[]")
    return data

def save_screening_answer(session_id, user_id, question_id, answer_text, numeric_score=None, input_mode="voice", raw_transcript=None):
    """Saves or updates a screening answer."""
    conn = get_db_connection()
    cursor = conn.cursor()
    ans_id = f"ans-{uuid.uuid4().hex[:8]}"
    
    # Check if answer already recorded for this session and question
    cursor.execute("""
    SELECT id FROM screening_answers WHERE session_id = ? AND question_id = ?
    """, (session_id, question_id))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute("""
        UPDATE screening_answers 
        SET answer_text = ?, numeric_score = ?, input_mode = ?, raw_transcript = ?, timestamp = CURRENT_TIMESTAMP
        WHERE id = ?
        """, (answer_text, numeric_score, input_mode, raw_transcript, existing["id"]))
    else:
        cursor.execute("""
        INSERT INTO screening_answers (id, session_id, user_id, question_id, answer_text, numeric_score, input_mode, raw_transcript)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (ans_id, session_id, user_id, question_id, answer_text, numeric_score, input_mode, raw_transcript))
        
    conn.commit()
    conn.close()
    return ans_id

def get_session_answers(session_id):
    """Retrieves all answers recorded for a screening session."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM screening_answers WHERE session_id = ? ORDER BY timestamp ASC
    """, (session_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_screening_session(session_id, **kwargs):
    """Updates fields in screening session."""
    conn = get_db_connection()
    cursor = conn.cursor()
    set_clauses = []
    values = []
    for k, v in kwargs.items():
        if k == "question_order" and isinstance(v, list):
            v = json.dumps(v)
        set_clauses.append(f"{k} = ?")
        values.append(v)
    values.append(session_id)
    
    query = f"UPDATE screening_sessions SET {', '.join(set_clauses)} WHERE id = ?"
    cursor.execute(query, tuple(values))
    conn.commit()
    conn.close()

def log_crisis_event(session_id, user_id, question_id, reason):
    """Logs a crisis trigger event."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE screening_sessions 
    SET status = 'crisis_halted', crisis_flag = 1, risk_flag = 'immediate',
        recommended_action = 'crisis_resources', completed_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (session_id,))
    conn.commit()
    conn.close()

# ----------------- PAST LIFE REFLECTION HELPERS ----------------- #

def create_past_life_session(session_id, user_id, conversation_id=None, language="en", interview_mode="short", total_questions=6):
    """Creates a new past life reflection session record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO past_life_sessions (id, user_id, conversation_id, language, interview_mode, status, current_index, total_questions)
    VALUES (?, ?, ?, ?, ?, 'in_progress', 0, ?)
    """, (session_id, user_id, conversation_id, language, interview_mode, total_questions))
    conn.commit()
    conn.close()
    return session_id

def update_past_life_session(session_id, **kwargs):
    """Updates fields of an active past life reflection session."""
    conn = get_db_connection()
    cursor = conn.cursor()
    set_clauses = []
    values = []
    for k, v in kwargs.items():
        set_clauses.append(f"{k} = ?")
        values.append(v)
    values.append(session_id)
    query = f"UPDATE past_life_sessions SET {', '.join(set_clauses)} WHERE id = ?"
    cursor.execute(query, tuple(values))
    conn.commit()
    conn.close()

def record_past_life_answer(session_id, user_id, question_id, theme, category, question_text, answer_text, input_mode="text", sentiment_score=0.0, emotional_themes=None):
    """Records an individual question response in the past life session."""
    conn = get_db_connection()
    cursor = conn.cursor()
    ans_id = f"pla_{str(uuid.uuid4())[:12]}"
    cursor.execute("""
    INSERT INTO past_life_answers (id, session_id, user_id, question_id, theme, category, question_text, answer_text, input_mode, sentiment_score, emotional_themes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ans_id,
        session_id,
        user_id,
        question_id,
        theme,
        category,
        question_text,
        answer_text,
        input_mode,
        sentiment_score,
        json.dumps(emotional_themes or [])
    ))
    conn.commit()
    conn.close()
    return ans_id

def get_past_life_session(session_id):
    """Fetches past life session details."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM past_life_sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_past_life_answers(session_id):
    """Fetches all recorded answers for a past life session."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM past_life_answers WHERE session_id = ? ORDER BY timestamp ASC", (session_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ----------------- EMOTION INTERVIEW HELPERS ----------------- #

def create_emotion_session(session_id: str, user_id: str, conversation_id: Optional[str] = None, language: str = "en", trigger_reason: Optional[str] = None, total_questions: int = 10):
    """Creates a new emotion interview session record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO emotion_interview_sessions (id, user_id, conversation_id, language, trigger_reason, status, current_index, total_questions)
    VALUES (?, ?, ?, ?, ?, 'in_progress', 0, ?)
    """, (session_id, user_id, conversation_id, language, trigger_reason, total_questions))
    conn.commit()
    conn.close()
    return session_id

def update_emotion_session(session_id: str, **kwargs):
    """Updates fields of an active emotion interview session."""
    conn = get_db_connection()
    cursor = conn.cursor()
    set_clauses = []
    values = []
    for k, v in kwargs.items():
        if isinstance(v, (list, dict)):
            v = json.dumps(v)
        set_clauses.append(f"{k} = ?")
        values.append(v)
    values.append(session_id)
    query = f"UPDATE emotion_interview_sessions SET {', '.join(set_clauses)} WHERE id = ?"
    cursor.execute(query, tuple(values))
    conn.commit()
    conn.close()

def record_emotion_answer(
    session_id: str,
    user_id: str,
    question_id: int,
    theme: str,
    question_text: str,
    answer_text: str,
    input_mode: str = "voice",
    detected_emotions: Optional[List[str]] = None,
    intensity: str = "moderate",
    sensitivity_flags: Optional[List[str]] = None
):
    """Records an individual question response in the emotion interview session."""
    conn = get_db_connection()
    cursor = conn.cursor()
    ans_id = f"emo_ans_{str(uuid.uuid4())[:12]}"
    cursor.execute("""
    INSERT INTO emotion_interview_answers (id, session_id, user_id, question_id, theme, question_text, answer_text, input_mode, detected_emotions, intensity, sensitivity_flags)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ans_id,
        session_id,
        user_id,
        question_id,
        theme,
        question_text,
        answer_text,
        input_mode,
        json.dumps(detected_emotions or []),
        intensity,
        json.dumps(sensitivity_flags or ["none"])
    ))
    conn.commit()
    conn.close()
    return ans_id

def get_emotion_session(session_id: str):
    """Fetches emotion interview session details."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM emotion_interview_sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_emotion_answers(session_id: str):
    """Fetches all recorded answers for an emotion interview session."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM emotion_interview_answers WHERE session_id = ? ORDER BY timestamp ASC", (session_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]



from werkzeug.security import generate_password_hash, check_password_hash

def create_user_with_password(name: str, email: str, password: str) -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if email exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return {"status": "error", "message": "Email already registered."}
        
    user_id = f"usr_{uuid.uuid4().hex[:12]}"
    p_hash = generate_password_hash(password)
    
    try:
        cursor.execute(
            "INSERT INTO users (id, name, email, password_hash) VALUES (?, ?, ?, ?)",
            (user_id, name, email, p_hash)
        )
        conn.commit()
    except Exception as e:
        conn.close()
        return {"status": "error", "message": str(e)}
        
    conn.close()
    return {"status": "success", "user_id": user_id, "name": name, "email": email}

def verify_user_login(email: str, password: str) -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, email, password_hash FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return {"status": "error", "message": "Invalid email or password."}
        
    if not user["password_hash"]:
        return {"status": "error", "message": "Account has no password set. Please use alternative login."}
        
    if check_password_hash(user["password_hash"], password):
        return {
            "status": "success",
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"]
            }
        }
        
    return {"status": "error", "message": "Invalid email or password."}
