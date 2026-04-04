"""
CedarCare - Database Seed Script
Automatically seeds the database with a demo account and sample
assessments on first startup. Safe to call multiple times —
uses IF NOT EXISTS checks to avoid duplicates.
"""

import json
import bcrypt
from datetime import datetime, timedelta
from components.database import get_connection, init_db

DEMO_EMAIL = "test@test.com"
DEMO_PASSWORD = "Password123"
DEMO_NAME = "Test User"


def seed_demo_user():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE email = ?", (DEMO_EMAIL,))
        existing = cursor.fetchone()
        if existing:
            print(f"[Seed] Demo user already exists (id={existing['id']})")
            return existing["id"]
        password_hash = bcrypt.hashpw(
            DEMO_PASSWORD.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        cursor.execute("""
            INSERT INTO users
                (name, email, password_hash, age, gender, region)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (DEMO_NAME, DEMO_EMAIL, password_hash, 30,
              "Prefer not to say", "Lower Mainland"))
        conn.commit()
        user_id = cursor.lastrowid
        print(f"[Seed] Demo user created (id={user_id})")
        return user_id
    except Exception as e:
        print(f"[Seed] Error creating demo user: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def seed_sample_assessments(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM assessments WHERE user_id = ?",
            (user_id,)
        )
        count = cursor.fetchone()["cnt"]
        if count > 0:
            print(f"[Seed] {count} assessments already exist — skipping.")
            return
        now = datetime.now()
        samples = [
            {
                "symptoms": "I have a runny nose and sore throat",
                "extracted_symptoms": json.dumps(["runny nose", "sore throat"]),
                "urgency_level": "Self-Care",
                "recommendation": "Rest, stay hydrated, and take OTC cold medication.",
                "days_ago": 30,
            },
            {
                "symptoms": "I have a fever and body aches",
                "extracted_symptoms": json.dumps(["fever", "body aches"]),
                "urgency_level": "Routine",
                "recommendation": "Visit a walk-in clinic if fever persists over 48 hours.",
                "days_ago": 20,
            },
            {
                "symptoms": "I have severe stomach pain",
                "extracted_symptoms": json.dumps(["stomach pain"]),
                "urgency_level": "Urgent",
                "recommendation": "Visit urgent care if pain worsens.",
                "days_ago": 10,
            },
            {
                "symptoms": "I have a mild headache",
                "extracted_symptoms": json.dumps(["headache"]),
                "urgency_level": "Self-Care",
                "recommendation": "Rest, drink water, take OTC pain relief if needed.",
                "days_ago": 5,
            },
            {
                "symptoms": "I have chest pain and left arm numbness",
                "extracted_symptoms": json.dumps(["chest pain", "arm numbness"]),
                "urgency_level": "Emergency",
                "recommendation": "Call 911 immediately.",
                "days_ago": 1,
            },
        ]
        for s in samples:
            created_at = (now - timedelta(days=s["days_ago"])).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            cursor.execute("""
                INSERT INTO assessments
                    (user_id, symptoms, extracted_symptoms,
                     urgency_level, recommendation, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                s["symptoms"],
                s["extracted_symptoms"],
                s["urgency_level"],
                s["recommendation"],
                created_at,
            ))
        conn.commit()
        print(f"[Seed] {len(samples)} sample assessments inserted.")
    except Exception as e:
        print(f"[Seed] Error seeding assessments: {e}")
        conn.rollback()
    finally:
        conn.close()


def run_seed():
    init_db()
    user_id = seed_demo_user()
    if user_id:
        seed_sample_assessments(user_id)


if __name__ == "__main__":
    run_seed()
