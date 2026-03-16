"""
Generate 5,000 synthetic health assessment records for the BC Health Platform.

Produces: Implementation/data/synthetic_assessments.csv
Dependencies: pandas, numpy (stdlib random)
Reproducible via seed 42.
"""

import os
import random

import numpy as np
import pandas as pd

# ============================================================================
# SEED
# ============================================================================
random.seed(42)
np.random.seed(42)

# ============================================================================
# CONSTANTS
# ============================================================================
TOTAL_RECORDS = 5000
NUM_PATIENTS = 200

CITIES = [
    "Vancouver", "Surrey", "Burnaby", "Richmond", "Kelowna",
    "Victoria", "Abbotsford", "Nanaimo", "Kamloops", "Prince George",
]

FIRST_NAMES_M = [
    "James", "John", "Robert", "Michael", "David", "William", "Richard",
    "Joseph", "Thomas", "Christopher", "Daniel", "Matthew", "Andrew",
    "Joshua", "Kevin", "Brian", "Ryan", "Jason", "Jeffrey", "Timothy",
    "Nathan", "Mark", "Steven", "Paul", "Edward", "Patrick", "Sean",
    "Kenneth", "Dennis", "Jerry", "Peter", "Henry", "Samuel", "Frank",
    "Gregory", "Raymond", "Benjamin", "Jack", "Lawrence", "Roger",
]
FIRST_NAMES_F = [
    "Mary", "Patricia", "Jennifer", "Linda", "Barbara", "Elizabeth",
    "Susan", "Jessica", "Sarah", "Karen", "Nancy", "Lisa", "Betty",
    "Dorothy", "Sandra", "Ashley", "Kimberly", "Emily", "Donna",
    "Michelle", "Carol", "Amanda", "Melissa", "Deborah", "Stephanie",
    "Rebecca", "Sharon", "Laura", "Cynthia", "Kathleen", "Amy",
    "Angela", "Shirley", "Anna", "Brenda", "Pamela", "Nicole",
    "Catherine", "Christine", "Samantha",
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
    "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Chen", "Wong", "Singh", "Patel", "Kim",
    "Sharma", "Ali", "Khan", "Das", "Kumar",
]

SYMPTOMS = [
    "headache", "fever", "cough", "sore throat", "fatigue", "nausea",
    "back pain", "chest pain", "shortness of breath", "dizziness",
    "runny nose", "muscle soreness", "abdominal pain", "rash",
    "joint pain", "high blood pressure", "diabetes symptoms",
    "anxiety", "depression", "insomnia",
]

FLU_SYMPTOMS = {"headache", "fever", "cough", "sore throat", "runny nose", "fatigue"}
CHRONIC_SYMPTOMS = {
    "chest pain", "shortness of breath", "high blood pressure",
    "diabetes symptoms", "joint pain",
}

# Symptom -> realistic diagnosis mapping
SYMPTOM_DIAGNOSIS = {
    "headache": ["Tension Headache", "Migraine", "Sinusitis"],
    "fever": ["Viral Infection", "Influenza", "Bacterial Infection"],
    "cough": ["Upper Respiratory Infection", "Bronchitis", "Allergic Cough"],
    "sore throat": ["Pharyngitis", "Tonsillitis", "Viral Sore Throat"],
    "fatigue": ["Chronic Fatigue", "Anemia", "Viral Infection"],
    "nausea": ["Gastritis", "Food Poisoning", "Gastroenteritis"],
    "back pain": ["Lumbar Strain", "Disc Herniation", "Muscle Spasm"],
    "chest pain": ["Angina", "Costochondritis", "GERD"],
    "shortness of breath": ["Asthma", "COPD Exacerbation", "Anxiety-Related Dyspnea"],
    "dizziness": ["Vertigo", "Orthostatic Hypotension", "Inner Ear Infection"],
    "runny nose": ["Allergic Rhinitis", "Common Cold", "Sinusitis"],
    "muscle soreness": ["Myalgia", "Fibromyalgia", "Overuse Injury"],
    "abdominal pain": ["Gastritis", "IBS Flare", "Appendicitis Concern"],
    "rash": ["Contact Dermatitis", "Eczema", "Allergic Reaction"],
    "joint pain": ["Osteoarthritis", "Rheumatoid Arthritis", "Gout"],
    "high blood pressure": ["Hypertension", "Hypertensive Episode", "White Coat Hypertension"],
    "diabetes symptoms": ["Type 2 Diabetes", "Hyperglycemia", "Pre-Diabetes"],
    "anxiety": ["Generalized Anxiety Disorder", "Panic Disorder", "Acute Stress Reaction"],
    "depression": ["Major Depressive Episode", "Dysthymia", "Adjustment Disorder"],
    "insomnia": ["Primary Insomnia", "Sleep Disorder", "Stress-Related Insomnia"],
}

URGENCY_LEVELS = ["Routine", "Moderate", "Urgent", "Emergency"]
URGENCY_WEIGHTS = {
    1: [0.70, 0.20, 0.08, 0.02],
    2: [0.50, 0.30, 0.15, 0.05],
    3: [0.30, 0.35, 0.28, 0.07],
}

RECOMMENDATION_MAP = {
    "Routine": "Home Care",
    "Moderate": "Call 811",
    "Urgent": "Walk-in Clinic",
    "Emergency": "ER",
}

# Date range: Mar 1 2025 - Mar 31 2026
DATE_START = pd.Timestamp("2025-03-01")
DATE_END = pd.Timestamp("2026-03-31")

# Flu season months (Nov-Feb)
FLU_MONTHS = {11, 12, 1, 2}


# ============================================================================
# STEP 1 — BUILD PATIENT POOL (200 patients)
# ============================================================================

def generate_patients():
    """Create 200 unique patients across three engagement tiers."""
    patients = []
    pid = 1

    tier_specs = [
        # (tier, count, age_lo, age_hi, freq_lo, freq_hi)
        (1, 80, 18, 45, 3, 8),
        (2, 80, 30, 65, 15, 25),
        (3, 40, 50, 85, 50, 80),
    ]

    used_names = set()

    for tier, count, age_lo, age_hi, freq_lo, freq_hi in tier_specs:
        for _ in range(count):
            gender = random.choice(["M", "F"])
            first_pool = FIRST_NAMES_M if gender == "M" else FIRST_NAMES_F
            # Ensure unique name
            while True:
                name = f"{random.choice(first_pool)} {random.choice(LAST_NAMES)}"
                if name not in used_names:
                    used_names.add(name)
                    break

            age = random.randint(age_lo, age_hi)
            city = random.choice(CITIES)
            yearly_freq = random.randint(freq_lo, freq_hi)

            patients.append({
                "patient_id": f"BC-{pid:04d}",
                "patient_name": name,
                "age": age,
                "gender": gender,
                "city": city,
                "tier": tier,
                "yearly_freq": yearly_freq,
            })
            pid += 1

    return patients


# ============================================================================
# STEP 2 — DISTRIBUTE 5,000 RECORDS ACROSS PATIENTS
# ============================================================================

def allocate_records(patients):
    """Distribute exactly 5,000 records respecting each patient's yearly_freq."""
    total_freq = sum(p["yearly_freq"] for p in patients)
    # Proportional allocation
    raw = [(p["yearly_freq"] / total_freq) * TOTAL_RECORDS for p in patients]
    counts = [max(1, int(r)) for r in raw]

    # Adjust to hit exactly 5,000
    diff = TOTAL_RECORDS - sum(counts)
    if diff > 0:
        # Add records to patients with highest fractional remainders
        remainders = [(raw[i] - counts[i], i) for i in range(len(patients))]
        remainders.sort(reverse=True)
        for k in range(diff):
            counts[remainders[k % len(remainders)][1]] += 1
    elif diff < 0:
        # Remove from patients with lowest fractional remainders (but keep >= 1)
        remainders = [(raw[i] - counts[i], i) for i in range(len(patients))]
        remainders.sort()
        removed = 0
        for _, idx in remainders:
            if removed >= abs(diff):
                break
            if counts[idx] > 1:
                counts[idx] -= 1
                removed += 1

    return counts


# ============================================================================
# STEP 3 — GENERATE ASSESSMENT DATES
# ============================================================================

def generate_dates(n):
    """Generate n dates in [DATE_START, DATE_END] with weekday bias."""
    total_days = (DATE_END - DATE_START).days
    dates = []
    for _ in range(n):
        while True:
            day_offset = random.randint(0, total_days)
            dt = DATE_START + pd.Timedelta(days=day_offset)
            # Weekdays (Mon-Fri) get accepted always; weekends accepted 60% of the time
            if dt.weekday() < 5 or random.random() < 0.60:
                dates.append(dt)
                break
    dates.sort()
    return dates


# ============================================================================
# STEP 4 — PICK SYMPTOMS WITH SEASONAL & TIER PATTERNS
# ============================================================================

def pick_symptom(tier, month):
    """Select a primary symptom with realistic weighting."""
    weights = []
    for s in SYMPTOMS:
        w = 1.0
        # Flu season boost
        if month in FLU_MONTHS and s in FLU_SYMPTOMS:
            w *= 1.4
        # Chronic tier boost
        if tier == 3 and s in CHRONIC_SYMPTOMS:
            w *= 2.5
        # Slight suppression of chronic symptoms for Tier 1
        if tier == 1 and s in CHRONIC_SYMPTOMS:
            w *= 0.3
        weights.append(w)

    total = sum(weights)
    probs = [w / total for w in weights]
    return np.random.choice(SYMPTOMS, p=probs)


# ============================================================================
# STEP 5 — BUILD ALL 5,000 RECORDS
# ============================================================================

def generate_records():
    patients = generate_patients()
    counts = allocate_records(patients)

    records = []

    for patient, n_records in zip(patients, counts):
        dates = generate_dates(n_records)

        for dt in dates:
            symptom = pick_symptom(patient["tier"], dt.month)
            diagnosis = random.choice(SYMPTOM_DIAGNOSIS[symptom])

            urgency = np.random.choice(
                URGENCY_LEVELS,
                p=URGENCY_WEIGHTS[patient["tier"]],
            )

            records.append({
                "patient_id": patient["patient_id"],
                "patient_name": patient["patient_name"],
                "age": patient["age"],
                "gender": patient["gender"],
                "city": patient["city"],
                "tier": patient["tier"],
                "assessment_date": dt.strftime("%Y-%m-%d"),
                "symptom": symptom,
                "diagnosis": diagnosis,
                "urgency_level": urgency,
                "recommendation": RECOMMENDATION_MAP[urgency],
                "assessment_duration_seconds": random.randint(120, 600),
                "confidence_score": round(random.uniform(0.65, 0.99), 2),
            })

    # ------------------------------------------------------------------
    # POST-GENERATION CHECK: cap Emergency at <= 5% (250 records)
    # ------------------------------------------------------------------
    emergency_cap = int(TOTAL_RECORDS * 0.05)  # 250
    emergency_indices = [i for i, r in enumerate(records) if r["urgency_level"] == "Emergency"]

    if len(emergency_indices) > emergency_cap:
        excess = len(emergency_indices) - emergency_cap
        downgrade = random.sample(emergency_indices, excess)
        for idx in downgrade:
            records[idx]["urgency_level"] = "Urgent"
            records[idx]["recommendation"] = RECOMMENDATION_MAP["Urgent"]

    return pd.DataFrame(records)


# ============================================================================
# MAIN
# ============================================================================

def main():
    df = generate_records()

    # Save CSV
    out_dir = os.path.join(os.path.dirname(__file__), "../../data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "synthetic_assessments.csv")
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} records to {os.path.abspath(out_path)}\n")

    # ------------------------------------------------------------------
    # VALIDATION SUMMARY
    # ------------------------------------------------------------------
    print("=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    # Total records
    print(f"\nTotal records generated: {len(df)}")

    # Urgency distribution
    print("\nUrgency distribution:")
    urgency_counts = df["urgency_level"].value_counts()
    for level in URGENCY_LEVELS:
        count = urgency_counts.get(level, 0)
        pct = count / len(df) * 100
        print(f"  {level:12s}: {count:5d}  ({pct:.1f}%)")

    # Emergency % confirmation
    emerg_pct = urgency_counts.get("Emergency", 0) / len(df) * 100
    print(f"\nEmergency % confirmation: {emerg_pct:.2f}% {'<= 5% OK' if emerg_pct <= 5.0 else 'EXCEEDS 5%!'}")

    # Top 5 symptoms
    print("\nTop 5 most common symptoms:")
    top5 = df["symptom"].value_counts().head(5)
    for symptom, count in top5.items():
        print(f"  {symptom:25s}: {count}")

    # Records per tier
    print("\nRecords per tier:")
    tier_counts = df["tier"].value_counts().sort_index()
    for tier, count in tier_counts.items():
        pct = count / len(df) * 100
        print(f"  Tier {tier}: {count:5d}  ({pct:.1f}%)")

    # Date range
    dates = pd.to_datetime(df["assessment_date"])
    print(f"\nDate range: {dates.min().strftime('%Y-%m-%d')} to {dates.max().strftime('%Y-%m-%d')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
