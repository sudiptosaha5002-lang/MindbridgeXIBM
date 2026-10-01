"""
Database management module for MindBridge.
Implements SQLite storage with PostgreSQL-compatible schema for users, 
conversations, messages, verified mental health providers, appointments, and consent.
"""

import sqlite3
import json
import os
import uuid
import math
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

    # Pharmacies & Online Medicine Platforms Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pharmacies (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        pharmacy_type TEXT NOT NULL, -- 'local' or 'online'
        address TEXT NOT NULL,
        locality TEXT,
        city TEXT NOT NULL,
        latitude REAL,
        longitude REAL,
        phone TEXT,
        whatsapp TEXT,
        hours TEXT DEFAULT '24/7 Open',
        rating REAL DEFAULT 4.8,
        review_count INTEGER DEFAULT 120,
        online_url TEXT,
        app_store_url TEXT,
        express_delivery TEXT DEFAULT 'Standard Delivery',
        delivery_available INTEGER DEFAULT 1,
        logo_badge TEXT,
        features TEXT, -- JSON array
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
    seed_pharmacies(cursor)
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
        },
        {
            "id": "clinic-narayana",
            "name": "Narayana Multispeciality Hospital",
            "type_pill": "Multi-Speciality Hospital · Salt Lake",
            "address": "Sector II, Bidhannagar, Salt Lake, Kolkata, West Bengal 700091",
            "locality": "Salt Lake, Kolkata",
            "city": "Kolkata",
            "state": "West Bengal",
            "latitude": 22.5870,
            "longitude": 88.4180,
            "phone": "+91 33 6680 0000",
            "website_url": "https://narayana.mindbridge.care",
            "features": json.dumps(["24/7 Emergency Dept", "Psychiatry & Behavioural Sciences", "In-patient Psychiatric Beds", "Online Hospital Appointments"]),
            "rating": 4.7
        },
        {
            "id": "clinic-apollo",
            "name": "Apollo Multispeciality Hospital",
            "type_pill": "Multi-Speciality Hospital · EM Bypass",
            "address": "11/1 Block A, EM Bypass, Kolkata, West Bengal 700099",
            "locality": "EM Bypass, Kolkata",
            "city": "Kolkata",
            "state": "West Bengal",
            "latitude": 22.5010,
            "longitude": 88.3920,
            "phone": "+91 33 6600 0000",
            "website_url": "https://apollo.mindbridge.care",
            "features": json.dumps(["24/7 Casualty & Trauma", "Department of Psychiatry", "Hospital Website Booking", "Critical Care & Neuro Sciences"]),
            "rating": 4.8
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
        if filters.get("hospital"):
            query += " AND hospital_id = ?"
            params.append(filters["hospital"])

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
    """Location-aware clinic/hospital directory with physical distance calculation and sorting."""
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
        features_val = item.get("features")
        if isinstance(features_val, str):
            try:
                item["features"] = json.loads(features_val)
            except Exception:
                item["features"] = []
        else:
            item["features"] = features_val or []
        results.append(item)

    conn.close()

    # If coordinates provided, compute physical Haversine distance from user's live position
    if filters and (filters.get("lat") is not None and (filters.get("lng") is not None or filters.get("lon") is not None)):
        try:
            u_lat = float(filters["lat"])
            u_lng = float(filters.get("lng") if filters.get("lng") is not None else filters.get("lon"))
            radius_m = float(filters.get("radiusMeters") or 60000)
            radius_km = radius_m / 1000.0

            for c in results:
                c_lat = c.get("latitude")
                c_lng = c.get("longitude")
                if c_lat is not None and c_lng is not None:
                    try:
                        c_lat_f = float(c_lat)
                        c_lng_f = float(c_lng)
                        R = 6371.0 # Earth's radius in km
                        dlat = math.radians(c_lat_f - u_lat)
                        dlng = math.radians(c_lng_f - u_lng)
                        a = (math.sin(dlat / 2) ** 2 +
                             math.cos(math.radians(u_lat)) * math.cos(math.radians(c_lat_f)) *
                             (math.sin(dlng / 2) ** 2))
                        dist_km = round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)
                        c["distance_km"] = dist_km
                        c["distance_meters"] = round(dist_km * 1000)
                        c["google_maps_directions"] = f"https://www.google.com/maps/dir/?api=1&origin={u_lat},{u_lng}&destination={c_lat_f},{c_lng_f}&travelmode=driving"
                    except Exception:
                        c["distance_km"] = None
                        c["distance_meters"] = None
                else:
                    c["distance_km"] = None
                    c["distance_meters"] = None

            # Sort ascending by distance (nearest first)
            results.sort(key=lambda x: (x["distance_km"] if x["distance_km"] is not None else 999999))
            
            # Prioritize clinics within radius_km (e.g. 60 km) so distant cities (Delhi, Bangalore) don't crowd the top
            nearby = [c for c in results if c.get("distance_km") is not None and c["distance_km"] <= radius_km]
            if len(nearby) >= 3:
                results = nearby
            else:
                # Keep the closest 8 regardless of radius
                results = results[:8]
        except (ValueError, TypeError):
            pass

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
    
    clean_email = email.strip().lower()
    clean_name = name.strip()
    
    # Strict case-insensitive check if email already registered
    cursor.execute("SELECT id FROM users WHERE LOWER(TRIM(email)) = LOWER(?)", (clean_email,))
    if cursor.fetchone():
        conn.close()
        return {
            "status": "error", 
            "code": "EMAIL_ALREADY_REGISTERED",
            "message": "This email address is already registered. Please sign in with your credentials or use another email."
        }
        
    user_id = f"usr_{uuid.uuid4().hex[:12]}"
    p_hash = generate_password_hash(password)
    
    try:
        cursor.execute(
            "INSERT INTO users (id, name, email, password_hash) VALUES (?, ?, ?, ?)",
            (user_id, clean_name, clean_email, p_hash)
        )
        conn.commit()
    except Exception as e:
        conn.close()
        return {"status": "error", "message": f"Registration failed: {str(e)}"}
        
    conn.close()
    return {"status": "success", "user_id": user_id, "name": clean_name, "email": clean_email}

def verify_user_login(email: str, password: str) -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    clean_email = email.strip().lower()
    
    cursor.execute("SELECT id, name, email, password_hash FROM users WHERE LOWER(TRIM(email)) = LOWER(?)", (clean_email,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return {
            "status": "error", 
            "code": "USER_NOT_FOUND",
            "message": "No account found with this email. Please check your credentials or register a new account."
        }
        
    if not user["password_hash"]:
        return {
            "status": "error", 
            "code": "NO_PASSWORD",
            "message": "Account credentials mismatch or password not configured."
        }
        
    if check_password_hash(user["password_hash"], password):
        return {
            "status": "success",
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"]
            }
        }
        
    return {
        "status": "error", 
        "code": "PASSWORD_MISMATCH",
        "message": "Invalid password. The credentials provided do not match our records."
    }


def seed_pharmacies(cursor):
    """Seed verified 24/7 local pharmacies and major online medicine delivery platforms."""
    cursor.execute("SELECT COUNT(*) as count FROM pharmacies")
    if cursor.fetchone()['count'] > 0:
        return

    sample_pharmacies = [
        # --- LOCAL 24/7 EMERGENCY PHARMACIES ---
        {
            "id": "pharm-1",
            "name": "Apollo Pharmacy 24/7 (Barasat Emergency Hub)",
            "pharmacy_type": "local",
            "address": "KNC Road, Near District Hospital, Barasat, Kolkata 700124",
            "locality": "Barasat",
            "city": "Kolkata",
            "latitude": 22.7095,
            "longitude": 88.4985,
            "phone": "+91 98301 23456",
            "whatsapp": "919830123456",
            "hours": "24/7 Open • Emergency Stocked",
            "rating": 4.9,
            "review_count": 210,
            "online_url": "https://www.apollo247.com/pharmacy",
            "app_store_url": "https://play.google.com/store/apps/details?id=com.apollo.patientapp",
            "express_delivery": "15-Min Express Pickup & Home Delivery",
            "delivery_available": 1,
            "logo_badge": "Apollo 24/7",
            "features": json.dumps(["24/7 Emergency Stock", "Insulin Cold Chain", "WhatsApp Orders", "Generic Medicine Discount"])
        },
        {
            "id": "pharm-2",
            "name": "Frank Ross Pharmacy 24/7 (Salt Lake Sector 1)",
            "pharmacy_type": "local",
            "address": "Block AB, Sector 1, Salt Lake City, Kolkata 700064",
            "locality": "Salt Lake",
            "city": "Kolkata",
            "latitude": 22.5878,
            "longitude": 88.4192,
            "phone": "+91 98302 34567",
            "whatsapp": "919830234567",
            "hours": "24/7 Open • Oxygen & ICU Care",
            "rating": 4.8,
            "review_count": 185,
            "online_url": "https://www.frankrosspharmacy.com",
            "app_store_url": "https://play.google.com/store/apps/details?id=com.frankross.app",
            "express_delivery": "30-Min Local Delivery",
            "delivery_available": 1,
            "logo_badge": "Frank Ross",
            "features": json.dumps(["24/7 Open", "ICU Equipment", "Home Delivery", "WhatsApp Ordering"])
        },
        {
            "id": "pharm-3",
            "name": "Sanjivani Emergency Chemist & Medicals (Bowbazar)",
            "pharmacy_type": "local",
            "address": "College Street Crossing, Bowbazar, Kolkata 700012",
            "locality": "Bowbazar",
            "city": "Kolkata",
            "latitude": 22.5632,
            "longitude": 88.3638,
            "phone": "+91 98303 45678",
            "whatsapp": "919830345678",
            "hours": "24/7 Open • Life Saving Drugs",
            "rating": 4.7,
            "review_count": 142,
            "online_url": "https://sanjivanimedicals.in",
            "app_store_url": "",
            "express_delivery": "Immediate Counter Pickup",
            "delivery_available": 1,
            "logo_badge": "Sanjivani",
            "features": json.dumps(["24/7 Emergency Stock", "WhatsApp Support", "Surgeons Supplies"])
        },
        {
            "id": "pharm-4",
            "name": "MedPlus 24x7 Emergency MedStore (College St)",
            "pharmacy_type": "local",
            "address": "122 College Street, Near Medical College Hospital, Kolkata 700073",
            "locality": "College Street",
            "city": "Kolkata",
            "latitude": 22.5742,
            "longitude": 88.3645,
            "phone": "+91 98304 56789",
            "whatsapp": "919830456789",
            "hours": "24/7 Open • 20% Discount",
            "rating": 4.8,
            "review_count": 310,
            "online_url": "https://www.medplusmart.com",
            "app_store_url": "https://play.google.com/store/apps/details?id=com.medplus.mart",
            "express_delivery": "Express Store Pickup & Local Dispatch",
            "delivery_available": 1,
            "logo_badge": "MedPlus",
            "features": json.dumps(["Flat 20% Off", "24/7 Open", "WhatsApp Orders", "Authentic Drugs"])
        },
        {
            "id": "pharm-5",
            "name": "LifeCare 24/7 Critical Medicine Hub (Saket Delhi)",
            "pharmacy_type": "local",
            "address": "Press Enclave Road, Opposite Max Super Speciality Hospital, Saket, New Delhi 110017",
            "locality": "Saket",
            "city": "New Delhi",
            "latitude": 28.5246,
            "longitude": 77.2190,
            "phone": "+91 98111 22334",
            "whatsapp": "919811122334",
            "hours": "24/7 Open • Oncology & ICU Drugs",
            "rating": 4.9,
            "review_count": 290,
            "online_url": "https://lifecaresaket.com",
            "app_store_url": "",
            "express_delivery": "20-Min Delhi NCR Dispatch",
            "delivery_available": 1,
            "logo_badge": "LifeCare",
            "features": json.dumps(["24/7 ICU Meds", "Cold Chain Insulin", "WhatsApp Orders"])
        },
        {
            "id": "pharm-6",
            "name": "Pulse Pharmacy & Critical Care (MG Road Bangalore)",
            "pharmacy_type": "local",
            "address": "MG Road, Near Fortis Emergency Gate, Bengaluru 560001",
            "locality": "MG Road",
            "city": "Bengaluru",
            "latitude": 12.9718,
            "longitude": 77.5948,
            "phone": "+91 98450 11223",
            "whatsapp": "919845011223",
            "hours": "24/7 Open • Express Delivery",
            "rating": 4.8,
            "review_count": 175,
            "online_url": "https://pulsepharmacy.in",
            "app_store_url": "",
            "express_delivery": "15-Min Bangalore Dispatch",
            "delivery_available": 1,
            "logo_badge": "Pulse Care",
            "features": json.dumps(["24/7 Open", "WhatsApp Prescriptions", "Cold Chain Storage"])
        },
        {
            "id": "pharm-7",
            "name": "Barasat 24/7 LifeLine Emergency Chemist",
            "pharmacy_type": "local",
            "address": "Station Road, Near District Hospital Gate, Barasat, North 24 Parganas, West Bengal 741201",
            "locality": "Barasat",
            "city": "Barasat",
            "latitude": 22.7231,
            "longitude": 88.4812,
            "phone": "+91 98308 99887",
            "whatsapp": "919830899887",
            "hours": "24/7 Open • Emergency Dispatch",
            "rating": 4.9,
            "review_count": 210,
            "online_url": "https://barasatlifeline.in",
            "app_store_url": "",
            "express_delivery": "15-Min Barasat Home Delivery",
            "delivery_available": 1,
            "logo_badge": "Barasat 24/7",
            "features": json.dumps(["24/7 Open", "WhatsApp Orders", "ICU & Oxygen Stock", "Home Delivery"])
        },
        {
            "id": "pharm-8",
            "name": "Apollo Pharmacy 24 Hours (Newtown Action Area 1)",
            "pharmacy_type": "local",
            "address": "Street No. 156, Action Area I, Newtown, Kolkata 700156",
            "locality": "Newtown",
            "city": "Kolkata",
            "latitude": 22.5855,
            "longitude": 88.4715,
            "phone": "+91 98319 77665",
            "whatsapp": "919831977665",
            "hours": "24/7 Open • Express Delivery",
            "rating": 4.8,
            "review_count": 340,
            "online_url": "https://www.apollopharmacy.in",
            "app_store_url": "https://play.google.com/store/apps/details?id=com.apollo.pharmacy",
            "express_delivery": "20-Min Newtown Delivery",
            "delivery_available": 1,
            "logo_badge": "Apollo 24/7",
            "features": json.dumps(["24/7 Open", "WhatsApp Prescriptions", "Cold Chain Insulin"])
        },

        # --- MAJOR ONLINE MEDICINE PLATFORMS ---
        {
            "id": "online-1",
            "name": "Tata 1mg",
            "pharmacy_type": "online",
            "address": "Online Delivery Platform (Pan-India)",
            "locality": "Pan-India",
            "city": "Online",
            "latitude": None,
            "longitude": None,
            "phone": "1800-212-2323",
            "whatsapp": "9118002122323",
            "hours": "24/7 Online Ordering",
            "rating": 4.9,
            "review_count": 15000,
            "online_url": "https://www.1mg.com",
            "app_store_url": "https://play.google.com/store/apps/details?id=com.arano.one_mg",
            "express_delivery": "Express 15-Min & Same-Day Delivery",
            "delivery_available": 1,
            "logo_badge": "Tata 1mg",
            "features": json.dumps(["Up to 25% Off", "Doctor Consultation", "Lab Tests at Home", "Genuine Medicines"])
        },
        {
            "id": "online-2",
            "name": "Amazon Pharmacy",
            "pharmacy_type": "online",
            "address": "Amazon Prime Medicine Delivery",
            "locality": "Pan-India",
            "city": "Online",
            "latitude": None,
            "longitude": None,
            "phone": "1800-3000-9009",
            "whatsapp": "",
            "hours": "24/7 Amazon Ordering",
            "rating": 4.8,
            "review_count": 12500,
            "online_url": "https://www.amazon.in/pharmacy",
            "app_store_url": "https://play.google.com/store/apps/details?id=in.amazon.mShop.android.shopping",
            "express_delivery": "Prime 2-Hour Express Delivery",
            "delivery_available": 1,
            "logo_badge": "Amazon Pharmacy",
            "features": json.dumps(["Prime 2-Hr Delivery", "100% Verified Prescriptions", "Easy Cashback"])
        },
        {
            "id": "online-3",
            "name": "Truemeds",
            "pharmacy_type": "online",
            "address": "Generic & Alternate Medicine Platform",
            "locality": "Pan-India",
            "city": "Online",
            "latitude": None,
            "longitude": None,
            "phone": "080-69808888",
            "whatsapp": "918069808888",
            "hours": "24/7 Orders Open",
            "rating": 4.7,
            "review_count": 9800,
            "online_url": "https://www.truemeds.in",
            "app_store_url": "https://play.google.com/store/apps/details?id=com.truemeds.app",
            "express_delivery": "Save Up to 72% on Generic Substitutes",
            "delivery_available": 1,
            "logo_badge": "Truemeds",
            "features": json.dumps(["72% Off Generic Meds", "Free Tele-Consultation", "Pan-India Shipping"])
        },
        {
            "id": "online-4",
            "name": "Apollo 24|7 Medicine",
            "pharmacy_type": "online",
            "address": "Apollo Healthcare & Pharmacy Digital Network",
            "locality": "Pan-India",
            "city": "Online",
            "latitude": None,
            "longitude": None,
            "phone": "1860-500-1066",
            "whatsapp": "9118605001066",
            "hours": "24/7 Emergency Support",
            "rating": 4.9,
            "review_count": 22000,
            "online_url": "https://www.apollo247.com/pharmacy",
            "app_store_url": "https://play.google.com/store/apps/details?id=com.apollo.patientapp",
            "express_delivery": "2-Hour Superfast Delivery",
            "delivery_available": 1,
            "logo_badge": "Apollo 24/7",
            "features": json.dumps(["2-Hour Delivery", "Apollo Circle Membership", "24/7 Doctor Helpline"])
        },
        {
            "id": "online-5",
            "name": "MedPlus Mart",
            "pharmacy_type": "online",
            "address": "MedPlus Omni-Channel Pharmacy",
            "locality": "Pan-India",
            "city": "Online",
            "latitude": None,
            "longitude": None,
            "phone": "040-67006700",
            "whatsapp": "914067006700",
            "hours": "24/7 Online Orders",
            "rating": 4.8,
            "review_count": 8900,
            "online_url": "https://www.medplusmart.com",
            "app_store_url": "https://play.google.com/store/apps/details?id=com.medplus.mart",
            "express_delivery": "Flat 20% Off + Express Pickup",
            "delivery_available": 1,
            "logo_badge": "MedPlus Mart",
            "features": json.dumps(["Flat 20% Off", "Flexi Store Pickup", "Authentic Prescriptions"])
        },
        {
            "id": "online-6",
            "name": "Dava India",
            "pharmacy_type": "online",
            "address": "Generic Medicine Revolution India",
            "locality": "Pan-India",
            "city": "Online",
            "latitude": None,
            "longitude": None,
            "phone": "1800-890-2270",
            "whatsapp": "",
            "hours": "24/7 Online Catalog",
            "rating": 4.7,
            "review_count": 6400,
            "online_url": "https://www.davaindia.com",
            "app_store_url": "https://play.google.com/store/apps/details?id=com.davaindia.app",
            "express_delivery": "Save Up to 90% on Medical Bills",
            "delivery_available": 1,
            "logo_badge": "Dava India",
            "features": json.dumps(["High Quality Generics", "Massive Savings", "Certified Labs"])
        }
    ]

    for p in sample_pharmacies:
        cursor.execute("""
        INSERT OR IGNORE INTO pharmacies (
            id, name, pharmacy_type, address, locality, city, latitude, longitude,
            phone, whatsapp, hours, rating, review_count, online_url, app_store_url,
            express_delivery, delivery_available, logo_badge, features, is_verified
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            p["id"], p["name"], p["pharmacy_type"], p["address"], p["locality"], p["city"],
            p["latitude"], p["longitude"], p["phone"], p["whatsapp"], p["hours"], p["rating"],
            p["review_count"], p["online_url"], p["app_store_url"], p["express_delivery"],
            p["delivery_available"], p["logo_badge"], p["features"]
        ))


def get_all_pharmacies(user_lat=None, user_lon=None, pharmacy_type=None, filter_tag=None, query=None):
    """Retrieve and proximity-sort local pharmacies and online medicine platforms."""
    conn = get_db_connection()
    cursor = conn.cursor()

    sql = "SELECT * FROM pharmacies WHERE is_verified = 1"
    params = []

    if pharmacy_type and pharmacy_type != 'all':
        sql += " AND pharmacy_type = ?"
        params.append(pharmacy_type)

    if filter_tag and filter_tag != 'all':
        if filter_tag == '24_7':
            sql += " AND (hours LIKE '%24/7%' OR hours LIKE '%24x7%' OR hours LIKE '%24 Hours%' OR features LIKE '%24/7%')"
        elif filter_tag == 'whatsapp':
            sql += " AND (whatsapp IS NOT NULL AND whatsapp != '' AND whatsapp != 'None')"
        elif filter_tag == 'express':
            sql += " AND (express_delivery LIKE '%Express%' OR express_delivery LIKE '%Min%' OR express_delivery LIKE '%Immediate%')"

    if query:
        sql += " AND (name LIKE ? OR locality LIKE ? OR city LIKE ? OR address LIKE ?)"
        q_wild = f"%{query}%"
        params.extend([q_wild, q_wild, q_wild, q_wild])

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    try:
        u_lat = float(user_lat) if (user_lat is not None and str(user_lat) != 'None') else 22.5626
        u_lon = float(user_lon) if (user_lon is not None and str(user_lon) != 'None') else 88.3630
    except (ValueError, TypeError):
        u_lat = 22.5626
        u_lon = 88.3630

    import math
    def haversine(lat1, lon1, lat2, lon2):
        if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
            return 999.0
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(R * c, 2)

    results = []
    for r in rows:
        item = dict(r)
        if item["features"]:
            try: item["features"] = json.loads(item["features"])
            except: item["features"] = []
        else:
            item["features"] = []

        if item["pharmacy_type"] == "local" and item["latitude"] and item["longitude"]:
            dist = haversine(u_lat, u_lon, item["latitude"], item["longitude"])
            item["distance_km"] = dist
            eta_mins = max(10, round(dist * 5))
            item["eta"] = f"{eta_mins}-{eta_mins + 10} mins"
        else:
            item["distance_km"] = 0.0
            item["eta"] = "Online Order"

        results.append(item)

    local_list = [p for p in results if p["pharmacy_type"] == "local"]
    online_list = [p for p in results if p["pharmacy_type"] == "online"]

    local_list.sort(key=lambda x: x["distance_km"])
    online_list.sort(key=lambda x: x["rating"], reverse=True)

    return {
        "local": local_list,
        "online": online_list,
        "all": local_list + online_list
    }
