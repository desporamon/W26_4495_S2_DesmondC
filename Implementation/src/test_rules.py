# Temporary test file - delete after verification

from components.rules import check_critical_symptoms

test_scenarios = [
    ("Heart Attack (Level 1)", ["chest pain", "shortness of breath"]),
    ("Stroke FAST Signs (Level 1)", ["face drooping", "arm weakness", "speech difficulty"]),
    ("Seizure (Level 1)", ["seizure"]),
    ("Chest Pain Alone (Level 2)", ["chest pain"]),
    ("Meningitis (Level 2)", ["severe headache", "stiff neck", "light sensitivity"]),
    ("Sore Throat - NOT critical", ["sore throat"]),
    ("Headache and Fatigue - NOT critical", ["headache", "fatigue"]),
]

print("=" * 60)
print("CTAS Rule-Based Safety Layer - Test Results")
print("=" * 60)

for description, symptoms in test_scenarios:
    result = check_critical_symptoms(symptoms)
    print(f"\nTest: {description}")
    print(f"  Symptoms: {symptoms}")
    if result["is_critical"]:
        print(f"  CRITICAL: Yes")
        print(f"  Rule:     {result['rule_name']}")
        print(f"  CTAS:     Level {result['ctas_level']}")
        print(f"  Action:   {result['action']}")
    else:
        print(f"  CRITICAL: No")
        print(f"  -> Passes to ML model")

print("\n" + "=" * 60)
print("Test complete.")
