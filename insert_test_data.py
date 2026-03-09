"""
insert_test_data.py
-------------------
# Synthetic test data for dashboard visualization testing — mirrors the exact format produced by the chatbot pipeline

Inserts ~70 assessment records for user_id=2 (Test User) into health_platform.db.
Spread across March 2025 – March 2026 with realistic monthly distribution.
Run once from the project root:
    python insert_test_data.py
"""

import sqlite3
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DB_PATH = Path(__file__).parent / "Implementation" / "data" / "health_platform.db"
USER_ID = 2
random.seed(42)  # reproducible

# ---------------------------------------------------------------------------
# Symptom definitions
# Each entry: (natural_language_description, extracted_symptoms_list, urgency_level, recommendation)
# ---------------------------------------------------------------------------
SYMPTOM_TEMPLATES = {
    "Emergency": [
        (
            "I have severe chest pain and difficulty breathing",
            ["chest pain", "difficulty breathing"],
            "Go to the nearest Emergency Room or CALL 911 immediately. This could be a cardiac event.",
        ),
        (
            "I suddenly can't move my left arm and my face is drooping",
            ["arm weakness", "facial drooping"],
            "Call 911 immediately. These are signs of a stroke — every minute counts.",
        ),
        (
            "I have severe chest tightness and my left arm feels numb",
            ["chest tightness", "arm numbness"],
            "Go to the Emergency Room immediately or call 911. This may be a heart attack.",
        ),
        (
            "I have a very high fever of 40°C and I'm having trouble breathing",
            ["high fever", "difficulty breathing"],
            "Go to Emergency immediately. Severe fever with breathing difficulty requires urgent evaluation.",
        ),
        (
            "I am having a severe allergic reaction with throat swelling",
            ["allergic reaction", "throat swelling"],
            "Call 911 now. Use your EpiPen if available. This is anaphylaxis.",
        ),
        (
            "I have severe abdominal pain that came on suddenly and I feel faint",
            ["severe abdominal pain", "dizziness", "fainting"],
            "Go to Emergency immediately. Sudden severe abdominal pain with dizziness requires urgent evaluation.",
        ),
        (
            "I am experiencing sudden severe headache, the worst headache of my life",
            ["sudden severe headache"],
            "Go to Emergency immediately. A sudden severe headache can indicate a brain bleed.",
        ),
    ],
    "Urgent": [
        (
            "I have had a fever of 39°C for two days and severe sore throat",
            ["fever", "sore throat"],
            "Visit a walk-in clinic today or tomorrow. You may need a strep test and antibiotics.",
        ),
        (
            "My back pain has been intense for three days and is spreading to my leg",
            ["back pain", "leg pain"],
            "See a doctor within 24 hours. Back pain radiating to the leg may need further evaluation.",
        ),
        (
            "I have had a pounding headache for two days with sensitivity to light",
            ["headache", "light sensitivity"],
            "Visit a walk-in clinic within 24 hours. A persistent headache with light sensitivity needs evaluation.",
        ),
        (
            "I have severe joint swelling and pain in my knee that started this morning",
            ["joint pain", "joint swelling"],
            "See a doctor within 24 hours. Sudden joint swelling may indicate infection or injury.",
        ),
        (
            "I have a skin rash spreading rapidly with blistering",
            ["skin rash", "blistering"],
            "Visit a walk-in clinic urgently. A spreading blistering rash needs prompt medical attention.",
        ),
        (
            "I have dizziness and feel like the room is spinning, also nauseous",
            ["dizziness", "nausea"],
            "Visit a walk-in clinic today. Vertigo with nausea should be evaluated.",
        ),
        (
            "I have a severe stomach ache and I vomited twice in the last hour",
            ["stomach pain", "vomiting"],
            "See a doctor within 24 hours. Persistent vomiting with stomach pain needs evaluation.",
        ),
        (
            "I have chest pain when I breathe in deeply",
            ["chest pain", "shortness of breath"],
            "Visit a walk-in clinic today. Pleuritic chest pain should be assessed.",
        ),
        (
            "I have a bad cough with yellowish phlegm and mild fever for four days",
            ["cough", "fever", "phlegm"],
            "Visit a walk-in clinic within 24 hours. You may have a chest infection.",
        ),
        (
            "I have high fever and ear pain that won't go away",
            ["high fever", "ear pain"],
            "See a doctor soon. Ear pain with fever may be an ear infection.",
        ),
        (
            "My stomach pain is severe and localized on the lower right side",
            ["stomach pain", "lower abdominal pain"],
            "Go to urgent care. Lower right abdominal pain can indicate appendicitis.",
        ),
        (
            "I have a bad migraine that has lasted over 24 hours",
            ["headache", "migraine"],
            "Visit a walk-in clinic. A migraine lasting over 24 hours needs medical attention.",
        ),
        (
            "I sprained my ankle badly and it is very swollen and bruised",
            ["joint pain", "swelling", "bruising"],
            "Go to urgent care or a walk-in clinic. You may need an X-ray to rule out a fracture.",
        ),
        (
            "I have had a high fever for three days and feel extremely fatigued",
            ["high fever", "fatigue"],
            "Visit a walk-in clinic today. Persistent high fever with fatigue needs evaluation.",
        ),
    ],
    "Routine": [
        (
            "I have had a mild headache since yesterday afternoon",
            ["headache"],
            "Book an appointment with your family doctor. Over-the-counter pain relief may help in the meantime.",
        ),
        (
            "My lower back has been aching for about a week",
            ["back pain"],
            "Consider booking with your family doctor. Gentle stretching and heat pads may provide relief.",
        ),
        (
            "I have had a runny nose and sore throat for three days",
            ["runny nose", "sore throat"],
            "Book an appointment with your family doctor if symptoms persist beyond a week.",
        ),
        (
            "I have been feeling very tired and low-energy for the past two weeks",
            ["fatigue"],
            "Schedule an appointment with your family doctor to discuss fatigue and possible causes.",
        ),
        (
            "I have noticed a rash on my arm that has been there for a few days",
            ["skin rash"],
            "Book a routine appointment with your family doctor or dermatologist.",
        ),
        (
            "I have mild stomach discomfort after eating for the past few days",
            ["stomach pain", "nausea"],
            "Consider booking with your family doctor. Avoid spicy and fatty foods in the meantime.",
        ),
        (
            "I have been getting recurring mild headaches for the past month",
            ["headache"],
            "Book an appointment with your family doctor to discuss recurring headaches.",
        ),
        (
            "I have mild joint pain in my fingers that is worse in the morning",
            ["joint pain"],
            "Book an appointment with your family doctor. Morning joint stiffness may need assessment.",
        ),
        (
            "I have had a persistent mild cough for about two weeks",
            ["cough"],
            "Book an appointment with your family doctor. A cough lasting more than two weeks should be checked.",
        ),
        (
            "I have been feeling dizzy in the mornings when I stand up quickly",
            ["dizziness"],
            "See your family doctor. Positional dizziness can be related to blood pressure or inner ear issues.",
        ),
        (
            "I have a mild skin rash on my back that is slightly itchy",
            ["skin rash", "itching"],
            "Book a routine appointment with your family doctor or dermatologist.",
        ),
        (
            "I have had a low-grade fever of 37.5°C for two days with general fatigue",
            ["fever", "fatigue"],
            "Monitor your symptoms. See your family doctor if fever persists beyond a few days.",
        ),
        (
            "I have stomach pain and bloating that comes and goes",
            ["stomach pain", "bloating"],
            "Book an appointment with your family doctor to discuss digestive symptoms.",
        ),
        (
            "My cough is producing some clear mucus and I have a mild sore throat",
            ["cough", "sore throat"],
            "Book an appointment with your family doctor if symptoms persist beyond 7–10 days.",
        ),
        (
            "I have been having mild back pain after sitting at my desk all day",
            ["back pain"],
            "Consider ergonomic adjustments at your workstation. Book with your family doctor if it persists.",
        ),
        (
            "I have occasional mild dizziness and slight nausea, mostly in the evening",
            ["dizziness", "nausea"],
            "Book an appointment with your family doctor to investigate the cause.",
        ),
        (
            "I have had a runny nose and watery eyes for several days",
            ["runny nose", "watery eyes"],
            "This may be seasonal allergies. Book with your family doctor or a pharmacist for advice.",
        ),
        (
            "I have mild chest discomfort and occasional cough after exercising",
            ["chest pain", "cough"],
            "Book an appointment with your family doctor. Exercise-induced symptoms should be evaluated.",
        ),
        (
            "I have recurring stomach cramps that usually occur after meals",
            ["stomach pain", "stomach cramps"],
            "Schedule an appointment with your family doctor to investigate possible IBS or food intolerances.",
        ),
        (
            "I have joint pain in my knees that has been bothering me for two weeks",
            ["joint pain"],
            "Book an appointment with your family doctor. Knee pain persisting over two weeks needs evaluation.",
        ),
        (
            "I have mild fatigue and trouble concentrating for the past few weeks",
            ["fatigue"],
            "Book an appointment with your family doctor. Consider discussing sleep habits and nutrition.",
        ),
        (
            "I have a runny nose, sneezing, and mild headache",
            ["runny nose", "headache", "sneezing"],
            "This sounds like a common cold. Rest and hydrate. See your doctor if symptoms worsen.",
        ),
        (
            "I have mild lower back pain that radiates slightly into my hip",
            ["back pain", "hip pain"],
            "Book an appointment with your family doctor. Back pain radiating to the hip may need assessment.",
        ),
        (
            "I have had a sore throat for five days and it hasn't improved",
            ["sore throat"],
            "Book an appointment with your family doctor. A sore throat lasting over five days should be checked.",
        ),
        (
            "I have mild skin redness on my face that is slightly warm to touch",
            ["skin rash", "facial redness"],
            "Book a routine appointment with your family doctor or dermatologist.",
        ),
        (
            "I have had mild headaches and slight neck stiffness for three days",
            ["headache", "neck stiffness"],
            "Book an appointment with your family doctor to rule out tension headaches or other causes.",
        ),
        (
            "I have a mild cough and feel more tired than usual",
            ["cough", "fatigue"],
            "Monitor your symptoms. Book with your family doctor if they persist beyond a week.",
        ),
        (
            "I have occasional sharp stomach pain that lasts a few minutes",
            ["stomach pain"],
            "Book an appointment with your family doctor to investigate recurring stomach pain.",
        ),
    ],
    "Self-Care": [
        (
            "I have a mild runny nose and sneezing",
            ["runny nose", "sneezing"],
            "You likely have a mild cold or allergies. Stay hydrated, rest, and consider antihistamines if needed.",
        ),
        (
            "I have mild muscle soreness after working out yesterday",
            ["muscle soreness", "fatigue"],
            "This is normal post-exercise soreness. Rest, hydrate, and consider a warm bath or gentle stretching.",
        ),
        (
            "I have a slight headache and feel a bit tired today",
            ["headache", "fatigue"],
            "Rest, hydrate well, and take over-the-counter pain relief if needed. Monitor symptoms.",
        ),
        (
            "I have a mild sore throat and feel slightly run down",
            ["sore throat"],
            "Rest and stay hydrated. Gargle with warm salt water. Monitor symptoms for improvement.",
        ),
        (
            "I have a mild cough with no fever and I feel okay otherwise",
            ["cough"],
            "Rest and stay hydrated. A mild cough without fever is usually self-limiting.",
        ),
        (
            "I have mild itchy eyes and a runny nose, likely seasonal allergies",
            ["runny nose", "itchy eyes"],
            "Consider over-the-counter antihistamines. Avoid allergen triggers. See your doctor if symptoms worsen.",
        ),
        (
            "I have mild back stiffness when I wake up in the morning",
            ["back pain"],
            "Try gentle morning stretches. Consider your sleeping position and mattress support.",
        ),
        (
            "I have very mild stomach discomfort after eating a heavy meal",
            ["stomach pain"],
            "Avoid heavy and spicy foods. Consider antacids if needed. Rest and monitor symptoms.",
        ),
        (
            "I feel slightly fatigued and my energy is a bit low today",
            ["fatigue"],
            "Ensure you are getting adequate sleep and nutrition. Rest and hydrate. Monitor if it persists.",
        ),
        (
            "I have a mildly stuffy nose and slight congestion",
            ["runny nose", "congestion"],
            "Use a saline nasal spray or humidifier. Stay hydrated. This is likely a mild cold.",
        ),
        (
            "I have mild eye strain and a slight headache after working on a screen all day",
            ["headache", "eye strain"],
            "Take regular breaks from your screen using the 20-20-20 rule. Ensure proper lighting.",
        ),
        (
            "I have minor skin dryness and some itching on my hands",
            ["skin rash", "itching"],
            "Apply moisturizing lotion regularly. Avoid harsh soaps. Consider a gentle hand cream.",
        ),
        (
            "I have mild bloating and gas after eating certain foods",
            ["stomach pain", "bloating"],
            "Avoid trigger foods (beans, dairy, carbonated drinks). Consider a food diary to identify patterns.",
        ),
        (
            "I have slight nasal congestion and a minor sore throat today",
            ["runny nose", "sore throat"],
            "Rest, stay hydrated, and gargle with warm salt water. This is likely the start of a common cold.",
        ),
        (
            "I feel mildly nauseous after eating but it passes quickly",
            ["nausea"],
            "Eat smaller, more frequent meals. Avoid greasy foods. Monitor if nausea persists or worsens.",
        ),
        (
            "I have minor muscle tension in my neck and shoulders",
            ["neck stiffness", "muscle soreness"],
            "Try gentle neck stretches and shoulder rolls. Consider heat therapy or a gentle massage.",
        ),
        (
            "I have mild seasonal allergy symptoms — sneezing and watery eyes",
            ["sneezing", "watery eyes"],
            "Consider over-the-counter antihistamines. Reduce exposure to outdoor allergens when pollen is high.",
        ),
        (
            "I have a slight cough and mild sore throat, probably from a dry environment",
            ["cough", "sore throat"],
            "Use a humidifier and stay hydrated. Honey and lemon in warm water may soothe your throat.",
        ),
        (
            "I have mild dizziness when I haven't eaten enough today",
            ["dizziness"],
            "Eat a balanced meal and hydrate. Low blood sugar can cause mild dizziness. Monitor if it continues.",
        ),
        (
            "I have minor joint aches, probably from overdoing it at the gym",
            ["joint pain", "muscle soreness"],
            "Rest the affected joints. Apply ice if swollen. Resume activity gradually when pain subsides.",
        ),
        (
            "I have a mild headache that usually comes in the afternoon",
            ["headache"],
            "Stay hydrated throughout the day. Dehydration is a common cause of afternoon headaches.",
        ),
    ],
}

# ---------------------------------------------------------------------------
# Monthly distribution weights: March 2025 (index 0) to March 2026 (index 12)
# More records in recent months, fewer in older months
# ---------------------------------------------------------------------------
MONTHS = [
    (2025, 3), (2025, 4), (2025, 5), (2025, 6),
    (2025, 7), (2025, 8), (2025, 9), (2025, 10),
    (2025, 11), (2025, 12), (2026, 1), (2026, 2), (2026, 3),
]
# Ascending weight: older months get fewer records, recent months get more
MONTH_WEIGHTS = [2, 2, 3, 3, 4, 4, 5, 5, 6, 7, 8, 10, 11]

# Urgency distribution: ~10% Emergency, ~20% Urgent, ~40% Routine, ~30% Self-Care
URGENCY_WEIGHTS = {"Emergency": 10, "Urgent": 20, "Routine": 40, "Self-Care": 30}
URGENCY_LEVELS = list(URGENCY_WEIGHTS.keys())
URGENCY_PROBS = [URGENCY_WEIGHTS[u] for u in URGENCY_LEVELS]


def pick_month() -> tuple:
    """Randomly pick a (year, month) tuple weighted toward recent months."""
    return random.choices(MONTHS, weights=MONTH_WEIGHTS, k=1)[0]


def pick_urgency() -> str:
    return random.choices(URGENCY_LEVELS, weights=URGENCY_PROBS, k=1)[0]


def pick_template(urgency: str) -> tuple:
    return random.choice(SYMPTOM_TEMPLATES[urgency])


def random_timestamp(year: int, month: int) -> str:
    """Return a random datetime string within the given month."""
    import calendar
    max_day = calendar.monthrange(year, month)[1]
    day = random.randint(1, max_day)
    hour = random.randint(7, 22)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"


# ---------------------------------------------------------------------------
# Build records
# ---------------------------------------------------------------------------
TARGET = 70
records = []

for _ in range(TARGET):
    year, month = pick_month()
    urgency = pick_urgency()
    description, extracted, recommendation = pick_template(urgency)
    ts = random_timestamp(year, month)
    records.append((USER_ID, description, json.dumps(extracted), urgency, recommendation, ts))

# Sort by timestamp so they look natural in the DB
records.sort(key=lambda r: r[5])

# ---------------------------------------------------------------------------
# Insert
# ---------------------------------------------------------------------------
conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

cursor.executemany("""
    INSERT INTO assessments (user_id, symptoms, extracted_symptoms, urgency_level, recommendation, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
""", records)

conn.commit()

cursor.execute("SELECT COUNT(*) FROM assessments WHERE user_id = ?", (USER_ID,))
total = cursor.fetchone()[0]
print(f"Inserted {len(records)} synthetic records for user_id={USER_ID}.")
print(f"Total assessment records for user_id={USER_ID}: {total}")

conn.close()
