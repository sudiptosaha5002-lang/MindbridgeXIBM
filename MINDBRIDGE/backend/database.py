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
        available_slots TEXT NOT NULL, -- JSON array
        locality TEXT,
        latitude REAL,
        longitude REAL,
        website_url TEXT,
        phone TEXT,
        hospital_id TEXT
    )
    """)

    # Migration for existing databases: fine-grained location + booking website + contact
    for col_def in (
        "locality TEXT",
        "latitude REAL",
        "longitude REAL",
        "website_url TEXT",
        "phone TEXT",
        "hospital_id TEXT",
    ):
        try:
            cursor.execute(f"ALTER TABLE providers ADD COLUMN {col_def}")
        except sqlite3.OperationalError:
            pass

    # Clinics / Hospitals Table (location-aware emergency clinical search)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clinics (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        type_pill TEXT NOT NULL,
        address TEXT NOT NULL,
        locality TEXT,
        city TEXT NOT NULL,
        state TEXT,
        latitude REAL,
        longitude REAL,
        phone TEXT,
        website_url TEXT,
        features TEXT NOT NULL, -- JSON array
        rating REAL DEFAULT 4.7,
        is_verified INTEGER DEFAULT 1
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
    seed_emergency_psychiatrists(cursor)
    apply_provider_geo_updates(cursor)
    seed_clinics(cursor)
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


def seed_emergency_psychiatrists(cursor):
    """Ensure city-wise psychiatrist specialists exist for Emergency Mode location listings (idempotent)."""
    emergency_psychiatrists = [
        {
            "id": "prov-psych-delhi",
            "name": "Dr. Sana Qureshi",
            "title": "Consultant Psychiatrist",
            "qualification": "MBBS, MD (Psychiatry), Member IPS",
            "experience_years": 14,
            "specializations": json.dumps(["Acute Anxiety & Panic", "Depression Crisis", "Suicidal Ideation Triage", "Medication Management"]),
            "languages": json.dumps(["English", "Hindi", "Urdu"]),
            "location_city": "New Delhi / Online Pan-India",
            "consultation_modes": json.dumps(["online", "in-person"]),
            "clinic_address": "Astitva Mind Clinic, Saket, New Delhi",
            "fee_per_session": 2100,
            "rating": 4.94,
            "reviews_count": 188,
            "avatar_url": "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=400&auto=format&fit=crop&q=80",
            "bio": "Dr. Qureshi provides emergency psychiatric evaluations, crisis de-escalation, and rapid medication review for patients experiencing severe anxiety, depressive episodes, or acute distress.",
            "available_days": json.dumps(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Sunday"]),
            "available_slots": json.dumps(["09:00 AM", "12:00 PM", "04:00 PM", "07:00 PM"])
        },
        {
            "id": "prov-psych-mumbai",
            "name": "Dr. Arjun Deshmukh",
            "title": "Consultant Psychiatrist",
            "qualification": "MBBS, DNB (Psychiatry), Certified Crisis Interventionist",
            "experience_years": 15,
            "specializations": json.dumps(["Bipolar Crisis", "Substance Use & Detox", "Panic Disorders", "Emergency Psychiatric Assessment"]),
            "languages": json.dumps(["English", "Hindi", "Marathi"]),
            "location_city": "Mumbai / Online Pan-India",
            "consultation_modes": json.dumps(["online", "in-person"]),
            "clinic_address": "Sanjeevani Neuropsychiatry Centre, Andheri West, Mumbai",
            "fee_per_session": 2400,
            "rating": 4.93,
            "reviews_count": 231,
            "avatar_url": "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=400&auto=format&fit=crop&q=80",
            "bio": "Dr. Deshmukh specialises in 24/7 acute psychiatric triage, bipolar mood stabilization, and supervised detox planning with compassionate, evidence-based care.",
            "available_days": json.dumps(["Monday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]),
            "available_slots": json.dumps(["10:00 AM", "01:00 PM", "05:00 PM", "08:00 PM"])
        },
        {
            "id": "prov-psych-kolkata",
            "name": "Dr. Sanjay Mehrotra",
            "title": "Senior Consultant Psychiatrist",
            "qualification": "MBBS, MD (Psychiatry - NIMHANS), FMH",
            "experience_years": 20,
            "specializations": json.dumps(["Severe Depression", "Psychosis Early Intervention", "Geriatric Psychiatry", "Crisis Counselling"]),
            "languages": json.dumps(["English", "Hindi", "Bengali"]),
            "location_city": "Kolkata / Online Pan-India",
            "consultation_modes": json.dumps(["online", "in-person"]),
            "clinic_address": "Mehrotra Mind Hospital, Ballygunge, Kolkata",
            "fee_per_session": 2500,
            "rating": 4.97,
            "reviews_count": 305,
            "avatar_url": "https://images.unsplash.com/photo-1537368910025-700350fe46c7?w=400&auto=format&fit=crop&q=80",
            "bio": "With two decades of emergency psychiatry experience, Dr. Mehrotra handles complex crisis presentations, treatment-resistant depression, and early psychotic interventions.",
            "available_days": json.dumps(["Tuesday", "Wednesday", "Thursday", "Saturday", "Sunday"]),
            "available_slots": json.dumps(["11:00 AM", "02:00 PM", "06:00 PM", "07:30 PM"])
        },
        {
            "id": "prov-psych-bengaluru",
            "name": "Dr. Vikramaditya Rao",
            "title": "Consultant Neuro-Psychiatrist",
            "qualification": "MBBS, MD (Psychiatry), DM (Neuropsychiatry)",
            "experience_years": 13,
            "specializations": json.dumps(["Neuropsychiatric Emergencies", "Severe OCD", "ADHD & Focus", "Sleep Crisis"]),
            "languages": json.dumps(["English", "Hindi", "Kannada", "Telugu"]),
            "location_city": "Bengaluru / Online Pan-India",
            "consultation_modes": json.dumps(["online", "in-person"]),
            "clinic_address": "Nirvana Neuropsychiatry Clinic, Koramangala, Bengaluru",
            "fee_per_session": 2300,
            "rating": 4.95,
            "reviews_count": 176,
            "avatar_url": "https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=400&auto=format&fit=crop&q=80",
            "bio": "Dr. Rao combines psychiatric emergency evaluation with advanced neuropsychiatric diagnostics, offering rapid relief pathways for acute distress and sleep collapse.",
            "available_days": json.dumps(["Monday", "Tuesday", "Thursday", "Friday", "Saturday"]),
            "available_slots": json.dumps(["09:30 AM", "01:30 PM", "04:30 PM", "07:00 PM"])
        },
        {
            "id": "prov-psych-chennai",
            "name": "Dr. Lakshmi Narayan",
            "title": "Consultant Psychiatrist",
            "qualification": "MBBS, MD (Psychiatry), Certificate in Emergency Mental Health",
            "experience_years": 11,
            "specializations": json.dumps(["Women's Mental Health", "Postpartum Crisis", "Anxiety & Panic", "Trauma-Informed Psychiatry"]),
            "languages": json.dumps(["English", "Tamil", "Hindi"]),
            "location_city": "Chennai / Online Pan-India",
            "consultation_modes": json.dumps(["online", "in-person"]),
            "clinic_address": "Serene Mind Psychiatry, Adyar, Chennai",
            "fee_per_session": 1900,
            "rating": 4.91,
            "reviews_count": 142,
            "avatar_url": "https://images.unsplash.com/photo-1594824813593-138382d56a34?w=400&auto=format&fit=crop&q=80",
            "bio": "Dr. Narayan offers 24/7 on-call psychiatric support with special focus on perinatal mental health emergencies, panic attacks, and trauma-sensitive stabilisation.",
            "available_days": json.dumps(["Monday", "Wednesday", "Friday", "Saturday", "Sunday"]),
            "available_slots": json.dumps(["10:30 AM", "12:30 PM", "03:30 PM", "06:30 PM"])
        },
        {
            "id": "prov-psych-hyderabad",
            "name": "Dr. Imran Haider",
            "title": "Consultant Psychiatrist & De-addiction Specialist",
            "qualification": "MBBS, MD (Psychiatry), FIAPM",
            "experience_years": 12,
            "specializations": json.dumps(["Addiction Crisis", "Withdrawal Management", "Depression", "Anger & Impulse Control"]),
            "languages": json.dumps(["English", "Hindi", "Telugu", "Urdu"]),
            "location_city": "Hyderabad / Online Pan-India",
            "consultation_modes": json.dumps(["online", "in-person"]),
            "clinic_address": "Haider Mind Care, Banjara Hills, Hyderabad",
            "fee_per_session": 2000,
            "rating": 4.90,
            "reviews_count": 158,
            "avatar_url": "https://images.unsplash.com/photo-1582750433449-648ed127bb54?w=400&auto=format&fit=crop&q=80",
            "bio": "Dr. Haider leads emergency de-addiction and withdrawal management pathways, combining psychiatric medication oversight with structured relapse-prevention therapy.",
            "available_days": json.dumps(["Monday", "Tuesday", "Wednesday", "Friday", "Saturday"]),
            "available_slots": json.dumps(["09:00 AM", "12:00 PM", "05:00 PM", "07:30 PM"])
        },
        {
            "id": "prov-psych-pune",
            "name": "Dr. Neha Bhatt",
            "title": "Consultant Psychiatrist",
            "qualification": "MBBS, DNB (Psychiatry), Certified CBT Psychiatrist",
            "experience_years": 10,
            "specializations": json.dumps(["Burnout & Exhaustion", "Exam & Performance Anxiety", "Insomnia", "Mood Disorders"]),
            "languages": json.dumps(["English", "Hindi", "Marathi", "Gujarati"]),
            "location_city": "Pune / Online Pan-India",
            "consultation_modes": json.dumps(["online", "in-person"]),
            "clinic_address": "MindSpring Psychiatry, Baner, Pune",
            "fee_per_session": 1800,
            "rating": 4.92,
            "reviews_count": 124,
            "avatar_url": "https://images.unsplash.com/photo-1651008376811-b90baee60c1f?w=400&auto=format&fit=crop&q=80",
            "bio": "Dr. Bhatt integrates psychiatric medication planning with CBT techniques for rapid relief from burnout, performance anxiety, and acute sleep disturbance.",
            "available_days": json.dumps(["Monday", "Tuesday", "Thursday", "Friday", "Sunday"]),
            "available_slots": json.dumps(["10:00 AM", "01:00 PM", "04:00 PM", "06:00 PM"])
        },
        {
            "id": "prov-psych-jaipur",
            "name": "Dr. Ritu Agarwal",
            "title": "Child & Adolescent Psychiatrist",
            "qualification": "MBBS, MD (Psychiatry), Fellowship in Child Psychiatry",
            "experience_years": 9,
            "specializations": json.dumps(["Adolescent Crisis", "Self-Harm Risk Assessment", "School Refusal", "Family Crisis Support"]),
            "languages": json.dumps(["English", "Hindi"]),
            "location_city": "Jaipur / Online Pan-India",
            "consultation_modes": json.dumps(["online", "in-person"]),
            "clinic_address": "Ujjwal Child & Mind Clinic, C-Scheme, Jaipur",
            "fee_per_session": 1700,
            "rating": 4.89,
            "reviews_count": 96,
            "avatar_url": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=400&auto=format&fit=crop&q=80",
            "bio": "Dr. Agarwal handles adolescent psychiatric emergencies including self-harm risk assessment, school refusal, and family-inclusive crisis stabilisation plans.",
            "available_days": json.dumps(["Monday", "Wednesday", "Thursday", "Saturday", "Sunday"]),
            "available_slots": json.dumps(["11:00 AM", "02:00 PM", "05:00 PM", "07:00 PM"])
        },
        {
            "id": "prov-psych-online",
            "name": "Dr. Kavya Iyer",
            "title": "Tele-Psychiatrist & Crisis Triage Specialist",
            "qualification": "MBBS, MD (Psychiatry), Tele-psychiatry Certified",
            "experience_years": 8,
            "specializations": json.dumps(["Pan-India Tele-psychiatry", "Same-day Crisis Consult", "Anxiety & Panic", "Prescription Review"]),
            "languages": json.dumps(["English", "Hindi", "Tamil", "Malayalam"]),
            "location_city": "Online Pan-India",
            "consultation_modes": json.dumps(["online"]),
            "clinic_address": "Virtual Crisis Psychiatric Desk, Pan-India",
            "fee_per_session": 1400,
            "rating": 4.93,
            "reviews_count": 210,
            "avatar_url": "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=400&auto=format&fit=crop&q=80",
            "bio": "Dr. Iyer operates a same-day tele-psychiatry desk for patients anywhere in India who need immediate psychiatric consultation, triage, and prescription review.",
            "locality": "Pan-India (Telehealth Desk)",
            "latitude": None,
            "longitude": None,
            "website_url": "https://kavyaiyer.telepsychiatry.mindbridge.care",
            "available_days": json.dumps(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]),
            "available_slots": json.dumps(["08:00 AM", "12:00 PM", "04:00 PM", "08:00 PM", "10:00 PM"])
        },
        {
            "id": "prov-psych-barasat",
            "name": "Dr. Ashim Chatterjee",
            "title": "Senior Consultant Psychiatrist",
            "qualification": "MBBS, MD (Psychiatry - IPGMER), Fellow Neuropsychiatry",
            "experience_years": 32,
            "specializations": json.dumps(["Geriatric Psychiatry", "Severe Depression", "Stroke & Brain-Mind Disorders", "Crisis De-escalation"]),
            "languages": json.dumps(["English", "Hindi", "Bengali"]),
            "location_city": "Barasat, North 24 Parganas / Online",
            "consultation_modes": json.dumps(["online", "in-person"]),
            "clinic_address": "Chatterjee Mind & Neuro Clinic, Grand Trunk Road, Barasat, North 24 Parganas, West Bengal 741201",
            "fee_per_session": 1600,
            "rating": 4.96,
            "reviews_count": 340,
            "avatar_url": "https://images.unsplash.com/photo-1537368910025-700350fe46c7?w=400&auto=format&fit=crop&q=80",
            "bio": "Dr. Chatterjee has served the Barasat and North 24 Parganas community for over three decades, handling geriatric psychiatry, post-stroke mood disorders, and acute crisis stabilisation.",
            "locality": "Barasat, North 24 Parganas",
            "latitude": 22.7200,
            "longitude": 88.4800,
            "website_url": "https://chatterjeemindclinic.mindbridge.care",
            "available_days": json.dumps(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]),
            "available_slots": json.dumps(["10:00 AM", "12:00 PM", "04:00 PM", "06:00 PM"])
        },
        {
            "id": "prov-psych-barasat2",
            "name": "Dr. Sanjana Bose",
            "title": "Consultant Psychiatrist",
            "qualification": "MBBS, DNB (Psychiatry), Member IPS",
            "experience_years": 11,
            "specializations": json.dumps(["Women's Mental Health", "Anxiety & Panic", "Adolescent Psychiatry", "Suicide Risk Assessment"]),
            "languages": json.dumps(["English", "Bengali", "Hindi"]),
            "location_city": "Barasat, North 24 Parganas / Online",
            "consultation_modes": json.dumps(["online", "in-person"]),
            "clinic_address": "Bose Mind Care Centre, Nabapally More, Barasat, North 24 Parganas, West Bengal 741203",
            "fee_per_session": 1400,
            "rating": 4.91,
            "reviews_count": 167,
            "avatar_url": "https://images.unsplash.com/photo-1594824813593-138382d56a34?w=400&auto=format&fit=crop&q=80",
            "bio": "Dr. Bose runs a neighbourhood psychiatric practice at Nabapally, Barasat — focused on same-week crisis appointments for anxiety, perinatal distress, and adolescent risk presentations.",
            "locality": "Barasat, North 24 Parganas",
            "latitude": 22.7280,
            "longitude": 88.4900,
            "website_url": "https://bosemindcare.mindbridge.care",
            "available_days": json.dumps(["Monday", "Wednesday", "Thursday", "Friday", "Sunday"]),
            "available_slots": json.dumps(["11:00 AM", "01:00 PM", "05:00 PM", "07:00 PM"])
        },
        {
            "id": "prov-psych-barasat3",
            "name": "Rupsa Dutta, M.Phil",
            "title": "Clinical Psychologist & Crisis Counsellor",
            "qualification": "M.Phil (Clinical Psychology), RCI Registered",
            "experience_years": 9,
            "specializations": json.dumps(["CBT Crisis De-escalation", "Trauma & Grief", "Student Distress", "Family Counselling"]),
            "languages": json.dumps(["English", "Bengali", "Hindi"]),
            "location_city": "Barasat, North 24 Parganas / Online",
            "consultation_modes": json.dumps(["online", "in-person"]),
            "clinic_address": "Dutta Psychology Studio, Rajbari Bazar, Barasat, North 24 Parganas, West Bengal 741201",
            "fee_per_session": 1100,
            "rating": 4.90,
            "reviews_count": 112,
            "avatar_url": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=400&auto=format&fit=crop&q=80",
            "bio": "Rupsa provides in-person and online crisis counselling in Barasat, specialising in CBT-based de-escalation for students, trauma recovery, and family conflicts.",
            "locality": "Barasat, North 24 Parganas",
            "latitude": 22.7150,
            "longitude": 88.4720,
            "website_url": "https://rupsadutta.mindbridge.care",
            "available_days": json.dumps(["Monday", "Tuesday", "Thursday", "Friday", "Saturday"]),
            "available_slots": json.dumps(["09:30 AM", "12:30 PM", "04:30 PM", "06:30 PM"])
        },
        {
            "id": "prov-psych-narayana",
            "name": "Dr. Arindam Ghosh",
            "title": "Consultant Psychiatrist · Narayana Multispeciality Hospital",
            "qualification": "MBBS, MD (Psychiatry), Member IPS",
            "experience_years": 14,
            "specializations": json.dumps(["Mood Disorders", "Hospital Liaison Psychiatry", "Anxiety & OCD", "Medication Review"]),
            "languages": json.dumps(["English", "Hindi", "Bengali"]),
            "location_city": "Salt Lake, Kolkata / Online",
            "consultation_modes": json.dumps(["online", "in-person"]),
            "clinic_address": "Narayana Multispeciality Hospital, Sector II, Bidhannagar, Salt Lake, Kolkata 700091",
            "fee_per_session": 2000,
            "rating": 4.92,
            "reviews_count": 154,
            "avatar_url": None,
            "bio": "Dr. Ghosh consults at Narayana Multispeciality Hospital, Salt Lake — inpatient/outpatient psychiatric liaison, mood-disorder management, and same-day hospital appointments via the hospital website.",
            "locality": "Salt Lake, Kolkata",
            "latitude": 22.5850,
            "longitude": 88.4150,
            "website_url": "https://narayana.mindbridge.care/book/dr-arindam-ghosh",
            "phone": "+91 33 6680 1122",
            "hospital_id": "clinic-narayana",
            "available_days": json.dumps(["Monday", "Tuesday", "Wednesday", "Friday", "Saturday"]),
            "available_slots": json.dumps(["10:00 AM", "12:00 PM", "04:00 PM", "06:00 PM"])
        },
        {
            "id": "prov-psych-apollo",
            "name": "Dr. Priyanka Sen",
            "title": "Consultant Psychiatrist · Apollo Multispeciality Hospital",
            "qualification": "MBBS, DNB (Psychiatry), Certified Consultation-Liaison Psychiatrist",
            "experience_years": 13,
            "specializations": json.dumps(["Consultation-Liaison Psychiatry", "Depression Crisis", "Women's Mental Health", "Sleep Disorders"]),
            "languages": json.dumps(["English", "Hindi", "Bengali"]),
            "location_city": "Kolkata / Online",
            "consultation_modes": json.dumps(["online", "in-person"]),
            "clinic_address": "Apollo Multispeciality Hospital, 11/1 Block A, EM Bypass, Kolkata 700099",
            "fee_per_session": 2200,
            "rating": 4.94,
            "reviews_count": 178,
            "avatar_url": None,
            "bio": "Dr. Sen sees patients at Apollo Multispeciality Hospital, Kolkata — psychiatric consultations coordinated through the hospital's appointment desk and website booking portal.",
            "locality": "EM Bypass, Kolkata",
            "latitude": 22.5000,
            "longitude": 88.3900,
            "website_url": "https://apollo.mindbridge.care/book/dr-priyanka-sen",
            "phone": "+91 33 6600 2233",
            "hospital_id": "clinic-apollo",
            "available_days": json.dumps(["Monday", "Tuesday", "Thursday", "Friday", "Sunday"]),
            "available_slots": json.dumps(["11:00 AM", "01:00 PM", "05:00 PM", "07:00 PM"])
        }
    ]

    for p in emergency_psychiatrists:
        cursor.execute("""
        INSERT OR IGNORE INTO providers (
            id, name, title, qualification, experience_years, specializations,
            languages, location_city, consultation_modes, clinic_address,
            fee_per_session, rating, reviews_count, avatar_url, bio, is_verified,
            available_days, available_slots, locality, latitude, longitude,
            website_url, phone, hospital_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p["id"], p["name"], p["title"], p["qualification"], p["experience_years"],
            p["specializations"], p["languages"], p["location_city"],
            p["consultation_modes"], p["clinic_address"], p["fee_per_session"],
            p["rating"], p["reviews_count"], p.get("avatar_url"), p["bio"],
            p.get("is_verified", 1), p["available_days"], p["available_slots"],
            p.get("locality"), p.get("latitude"), p.get("longitude"),
            p.get("website_url"), p.get("phone"), p.get("hospital_id")
        ))


# Fine-grained locality / coordinates / booking website for every known provider
PROVIDER_GEO_UPDATES = {
    "prov-1": ("Vasant Vihar, New Delhi", 28.5590, 77.1600, "https://ananyasharma.mindbridge.care"),
    "prov-2": ("Salt Lake Sector 1, Kolkata", 22.5800, 88.4200, "https://rajeshvarma.mindbridge.care"),
    "prov-3": ("Bandra West, Mumbai", 19.0590, 72.8290, "https://meerasen.mindbridge.care"),
    "prov-4": ("Indiranagar, Bengaluru", 12.9780, 77.6400, "https://karthiksundaram.mindbridge.care"),
    "prov-5": ("Kolkata (Tele-therapy)", 22.5726, 88.3639, "https://priyankaroy.mindbridge.care"),
    "prov-psych-delhi": ("Saket, New Delhi", 28.5240, 77.2060, "https://sanaqureshi.mindbridge.care"),
    "prov-psych-mumbai": ("Andheri West, Mumbai", 19.1350, 72.8260, "https://arjundeshmukh.mindbridge.care"),
    "prov-psych-kolkata": ("Ballygunge, Kolkata", 22.5250, 88.3630, "https://sanjaymehrotra.mindbridge.care"),
    "prov-psych-bengaluru": ("Koramangala, Bengaluru", 12.9350, 77.6240, "https://vikramrao.mindbridge.care"),
    "prov-psych-chennai": ("Adyar, Chennai", 13.0010, 80.2560, "https://lakshminarayan.mindbridge.care"),
    "prov-psych-hyderabad": ("Banjara Hills, Hyderabad", 17.4120, 78.4350, "https://imranhaider.mindbridge.care"),
    "prov-psych-pune": ("Baner, Pune", 18.5640, 73.7770, "https://nehabhatt.mindbridge.care"),
    "prov-psych-jaipur": ("C-Scheme, Jaipur", 26.9090, 75.7990, "https://rituagarwal.mindbridge.care"),
    "prov-psych-online": ("Pan-India (Telehealth Desk)", None, None, "https://kavyaiyer.telepsychiatry.mindbridge.care"),
    "prov-psych-barasat": ("Barasat, North 24 Parganas", 22.7200, 88.4800, "https://chatterjeemindclinic.mindbridge.care"),
    "prov-psych-barasat2": ("Barasat, North 24 Parganas", 22.7280, 88.4900, "https://bosemindcare.mindbridge.care"),
    "prov-psych-barasat3": ("Barasat, North 24 Parganas", 22.7150, 88.4720, "https://rupsadutta.mindbridge.care"),
    "prov-psych-narayana": ("Salt Lake, Kolkata", 22.5850, 88.4150, "https://narayana.mindbridge.care/book/dr-arindam-ghosh"),
    "prov-psych-apollo": ("EM Bypass, Kolkata", 22.5000, 88.3900, "https://apollo.mindbridge.care/book/dr-priyanka-sen"),
}

# Clinic phone number + affiliated hospital (dropdown selection) for every provider
PROVIDER_CONTACT = {
    "prov-1": ("+91 11 4102 5566", None),
    "prov-2": ("+91 33 2337 1122", "clinic-kolkata-neuro"),
    "prov-3": ("+91 22 2640 3344", None),
    "prov-4": ("+91 80 4155 6677", "clinic-nimhans"),
    "prov-5": ("+91 33 4004 1155", None),
    "prov-psych-delhi": ("+91 11 4288 9900", "clinic-saket"),
    "prov-psych-mumbai": ("+91 22 2673 4455", "clinic-andheri"),
    "prov-psych-kolkata": ("+91 33 2461 8899", "clinic-kolkata-neuro"),
    "prov-psych-bengaluru": ("+91 80 4123 7788", "clinic-nimhans"),
    "prov-psych-chennai": ("+91 44 4211 3344", "clinic-chennai"),
    "prov-psych-hyderabad": ("+91 40 2331 5566", "clinic-hyd-neuro"),
    "prov-psych-pune": ("+91 20 2721 4455", "clinic-pune-bhc"),
    "prov-psych-jaipur": ("+91 141 236 7788", "clinic-jaipur-cmc"),
    "prov-psych-online": ("+91 80 4004 1188", None),
    "prov-psych-barasat": ("+91 33 2562 1144", "clinic-barasat-dh"),
    "prov-psych-barasat2": ("+91 33 2562 2255", "clinic-barasat-dh"),
    "prov-psych-barasat3": ("+91 33 2562 3366", "clinic-barasat-mind"),
    "prov-psych-narayana": ("+91 33 6680 1122", "clinic-narayana"),
    "prov-psych-apollo": ("+91 33 6600 2233", "clinic-apollo"),
}


def apply_provider_geo_updates(cursor):
    """Backfill locality, coordinates, website, phone, hospital + strip stock model photos (idempotent)."""
    for pid, (locality, lat, lon, website) in PROVIDER_GEO_UPDATES.items():
        cursor.execute("""
        UPDATE providers
        SET locality = ?, latitude = ?, longitude = ?, website_url = ?
        WHERE id = ?
        """, (locality, lat, lon, website, pid))
    for pid, (phone, hospital_id) in PROVIDER_CONTACT.items():
        cursor.execute("""
        UPDATE providers SET phone = ?, hospital_id = ? WHERE id = ?
        """, (phone, hospital_id, pid))
    # Seniority bumps so the Experience filter (25+/30+) has real matches
    for pid, years in (("prov-psych-kolkata", 26), ("prov-2", 18)):
        cursor.execute("UPDATE providers SET experience_years = ? WHERE id = ?", (years, pid))
    # Never show stock/model photos — blank DP unless a REAL doctor photo exists
    cursor.execute("UPDATE providers SET avatar_url = NULL WHERE avatar_url LIKE '%unsplash%'")


def seed_clinics(cursor):
    """Seed location-aware emergency clinics/hospitals (idempotent)."""
    clinics = [
        {
            "id": "clinic-barasat-dh",
            "name": "Barasat District Hospital",
            "type_pill": "Govt. District Hospital · 24/7 Emergency",
            "address": "Station Road, Barasat, North 24 Parganas, West Bengal 741201",
            "locality": "Barasat, North 24 Parganas",
            "city": "Kolkata",
            "state": "West Bengal",
            "latitude": 22.7210,
            "longitude": 88.4820,
            "phone": "+91 33 2562 3000",
            "website_url": "https://barasatdistrict.mindbridge.care",
            "features": json.dumps(["24/7 Casualty & Triage", "Psychiatric Emergency Desk", "Govt. Subsidized", "Ambulance Station"]),
            "rating": 4.5
        },
        {
            "id": "clinic-barasat-mind",
            "name": "Shanti Mind Clinic & Day Care",
            "type_pill": "Private Psychiatric Clinic · Barasat",
            "address": "NB Block, Rajbari Bazar, Barasat, North 24 Parganas, West Bengal 741201",
            "locality": "Barasat, North 24 Parganas",
            "city": "Kolkata",
            "state": "West Bengal",
            "latitude": 22.7180,
            "longitude": 88.4760,
            "phone": "+91 33 2562 7788",
            "website_url": "https://shantimind.mindbridge.care",
            "features": json.dumps(["Day-Care Crisis Ward", "De-addiction Counselling", "Family Therapy Rooms", "Same-week Appointments"]),
            "rating": 4.7
        },
        {
            "id": "clinic-barrackpore",
            "name": "North 24 Parganas Mental Health Centre",
            "type_pill": "Sub-divisional Mental Health Unit",
            "address": "Barrackpore Court Road, North 24 Parganas, West Bengal 743101",
            "locality": "Barrackpore, North 24 Parganas",
            "city": "Kolkata",
            "state": "West Bengal",
            "latitude": 22.7850,
            "longitude": 88.3700,
            "phone": "+91 33 2591 4400",
            "website_url": "https://n24mentalhealth.mindbridge.care",
            "features": json.dumps(["Crisis Observation Beds", "Tele-psychiatry Link", "Govt. Subsidized", "District Mobile Team"]),
            "rating": 4.4
        },
        {
            "id": "clinic-nimhans",
            "name": "National Institute of Mental Health & Neuro Sciences (NIMHANS)",
            "type_pill": "National Apex Institute · 24/7 Emergency",
            "address": "Hosur Road, Lakkasandra, Bengaluru, Karnataka 560029",
            "locality": "Lakkasandra, Bengaluru",
            "city": "Bengaluru",
            "state": "Karnataka",
            "latitude": 12.9430,
            "longitude": 77.5950,
            "phone": "+91 80 2699 5000",
            "website_url": "https://nimhans.mindbridge.care",
            "features": json.dumps(["24/7 Crisis Inpatient Beds", "Psychiatric Casualty", "Resident Psychiatrists", "Govt. Subsidized"]),
            "rating": 4.9
        },
        {
            "id": "clinic-aiims",
            "name": "AIIMS Department of Psychiatry & Emergency Behavioral Ward",
            "type_pill": "Comprehensive Care Center · Emergency Dept",
            "address": "Sri Aurobindo Marg, Ansari Nagar, New Delhi 110029",
            "locality": "Ansari Nagar, New Delhi",
            "city": "New Delhi",
            "state": "Delhi",
            "latitude": 28.5670,
            "longitude": 77.2100,
            "phone": "+91 11 2658 8500",
            "website_url": "https://aiimspsychiatry.mindbridge.care",
            "features": json.dumps(["Intensive Psychiatric Care (IPC)", "Neuro-toxicology & Crisis", "24-Hour Emergency Triage"]),
            "rating": 4.9
        },
        {
            "id": "clinic-fortis",
            "name": "Fortis Mental Health & Emergency Clinical Sciences",
            "type_pill": "Multi-Specialty Private Care · Rapid Triage",
            "address": "Sector 44, Opposite Huda City Centre, Gurugram, Haryana 122002",
            "locality": "Sector 44, Gurugram",
            "city": "Gurugram",
            "state": "Haryana",
            "latitude": 28.4590,
            "longitude": 77.0260,
            "phone": "+91 124 4962 200",
            "website_url": "https://fortismentalhealth.mindbridge.care",
            "features": json.dumps(["Private Suites & Crisis Ward", "24/7 Dedicated Ambulance", "Certified Clinical Psychologists"]),
            "rating": 4.6
        },
        {
            "id": "clinic-kolkata-neuro",
            "name": "Institute of Neurosciences & Psychiatric Care, Kolkata",
            "type_pill": "Specialty Neuroscience Institute",
            "address": "58 Canal West Road, Burtalla, Sealdah, Kolkata, West Bengal 700014",
            "locality": "Sealdah, Kolkata",
            "city": "Kolkata",
            "state": "West Bengal",
            "latitude": 22.5620,
            "longitude": 88.3710,
            "phone": "+91 33 2265 1100",
            "website_url": "https://kolkataneuro.mindbridge.care",
            "features": json.dumps(["Neuro-Psychiatry Wards", "EEG & Neuro-imaging", "Stroke Rehab & Mind Care", "24/7 On-call Psychiatrist"]),
            "rating": 4.8
        },
        {
            "id": "clinic-saket",
            "name": "Saket Mind Care Hospital",
            "type_pill": "Private Psychiatric Hospital · South Delhi",
            "address": "Press Enclave Road, Saket, New Delhi 110017",
            "locality": "Saket, New Delhi",
            "city": "New Delhi",
            "state": "Delhi",
            "latitude": 28.5200,
            "longitude": 77.2100,
            "phone": "+91 11 4155 6600",
            "website_url": "https://saketmind.mindbridge.care",
            "features": json.dumps(["In-patient Psychiatry", "De-addiction Unit", "Child & Adolescent Wing", "24/7 Crisis Helpline Desk"]),
            "rating": 4.7
        },
        {
            "id": "clinic-andheri",
            "name": "Andheri West Psychiatric Centre",
            "type_pill": "Private Psychiatric Centre · Mumbai",
            "address": "Veera Desai Road, Andheri West, Mumbai, Maharashtra 400058",
            "locality": "Andheri West, Mumbai",
            "city": "Mumbai",
            "state": "Maharashtra",
            "latitude": 19.1320,
            "longitude": 72.8240,
            "phone": "+91 22 4267 8800",
            "website_url": "https://andheripsych.mindbridge.care",
            "features": json.dumps(["Day Care Crisis Beds", "Substance Use Programme", "Couples & Family Clinic", "Evening Emergency Slots"]),
            "rating": 4.6
        },
        {
            "id": "clinic-chennai",
            "name": "Chennai Mind Hospital",
            "type_pill": "Specialty Mental Health Hospital · Adyar",
            "address": "1st Avenue, Adyar, Chennai, Tamil Nadu 600020",
            "locality": "Adyar, Chennai",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "latitude": 13.0030,
            "longitude": 80.2570,
            "phone": "+91 44 4284 5500",
            "website_url": "https://chennaimind.mindbridge.care",
            "features": json.dumps(["24/7 Psychiatric Casualty", "ECT & Neuro-modulation", "Perinatal Mental Health Unit", "Rehab Day Centre"]),
            "rating": 4.8
        },
        {
            "id": "clinic-hyd-neuro",
            "name": "Hyderabad Neuropsychiatry Centre",
            "type_pill": "Neuropsychiatry & De-addiction · Banjara Hills",
            "address": "Road No. 12, Banjara Hills, Hyderabad, Telangana 500034",
            "locality": "Banjara Hills, Hyderabad",
            "city": "Hyderabad",
            "state": "Telangana",
            "latitude": 17.4140,
            "longitude": 78.4360,
            "phone": "+91 40 2354 9900",
            "website_url": "https://hydneuropsych.mindbridge.care",
            "features": json.dumps(["Withdrawal Management Unit", "24/7 Crisis Beds", "Neuro-rehabilitation", "Family De-addiction Counselling"]),
            "rating": 4.7
        },
        {
            "id": "clinic-pune-bhc",
            "name": "Pune Behavioural Health Centre",
            "type_pill": "Behavioural Sciences Hospital · Baner",
            "address": "Baner Road, near Balewadi Phata, Pune, Maharashtra 411045",
            "locality": "Baner, Pune",
            "city": "Pune",
            "state": "Maharashtra",
            "latitude": 18.5630,
            "longitude": 73.7760,
            "phone": "+91 20 6720 1100",
            "website_url": "https://punebhc.mindbridge.care",
            "features": json.dumps(["Acute Psychiatric Wards", "Sleep & Stress Lab", "Corporate Burnout Programme", "24/7 Duty Psychiatrist"]),
            "rating": 4.6
        },
        {
            "id": "clinic-jaipur-cmc",
            "name": "Jaipur Child & Mind Clinic",
            "type_pill": "Child & Adolescent Mental Health · C-Scheme",
            "address": "Ashok Marg, C-Scheme, Jaipur, Rajasthan 302001",
            "locality": "C-Scheme, Jaipur",
            "city": "Jaipur",
            "state": "Rajasthan",
            "latitude": 26.9080,
            "longitude": 75.7990,
            "phone": "+91 141 237 4400",
            "website_url": "https://jaipurchildmind.mindbridge.care",
            "features": json.dumps(["Adolescent Crisis Desk", "School Refusal Programme", "Play & Art Therapy Rooms", "Parent Guidance Clinic"]),
            "rating": 4.7
        }
    ]

    for c in clinics:
        cursor.execute("""
        INSERT OR IGNORE INTO clinics (
            id, name, type_pill, address, locality, city, state,
            latitude, longitude, phone, website_url, features, rating, is_verified
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            c["id"], c["name"], c["type_pill"], c["address"], c["locality"],
            c["city"], c["state"], c["latitude"], c["longitude"], c["phone"],
            c["website_url"], c["features"], c["rating"]
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
        if filters.get("location"):
            query += " AND location_city LIKE ?"
            params.append(f"%{filters['location']}%")
        if filters.get("min_experience"):
            query += " AND experience_years >= ?"
            params.append(filters["min_experience"])
        if filters.get("min_rating"):
            query += " AND rating >= ?"
            params.append(filters["min_rating"])

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

def get_all_clinics(filters=None):
    """Location-aware clinic/hospital directory."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM clinics WHERE is_verified = 1"
    params = []

    if filters:
        if filters.get("location"):
            query += " AND (address LIKE ? OR locality LIKE ? OR city LIKE ? OR name LIKE ?)"
            like = f"%{filters['location']}%"
            params.extend([like, like, like, like])

    query += " ORDER BY rating DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()

    results = []
    for r in rows:
        item = dict(r)
        item["features"] = json.loads(item["features"])
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
