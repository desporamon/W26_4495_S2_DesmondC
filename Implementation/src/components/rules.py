# =============================================================================
# BC Health Platform - CTAS Rule-Based Safety Layer
# =============================================================================
# Based on CTAS Implementation Guidelines (2008) - Canadian Emergency
# Department Triage & Acuity Scale
# =============================================================================
# MEDICAL DISCLAIMER:
# This tool is for informational purposes only and does not replace
# professional medical advice. Always consult a qualified healthcare
# provider for medical concerns. If you are experiencing a medical
# emergency, call 911 immediately.
# =============================================================================

"""
CTAS (Canadian Triage and Acuity Scale) rule-based safety layer for the
BC Health Platform Symptom Assessment Chatbot.

This module is Step 2 in the 3-layer hybrid classification system:
    Step 1: OpenAI  - Extract structured symptoms from natural language
    Step 2: Rules   - Catch life-threatening emergencies (THIS MODULE)
    Step 3: ML      - Classify non-critical symptoms with a trained model

The purpose of this safety layer is to catch life-threatening emergencies
BEFORE the ML model runs, ensuring 100% reliability for critical symptoms.
Rule-based checks never depend on model predictions — they use deterministic
keyword matching so that critical conditions are never missed.

CTAS Levels:
    Level 1 - Resuscitation: Immediate threat to life (e.g., cardiac arrest)
    Level 2 - Emergent:      Potential threat to life or limb (e.g., chest pain)
    Level 3 - Urgent:        Could progress to serious problem (e.g., asthma)
    Level 4 - Less Urgent:   Related to patient age/distress (e.g., earache)
    Level 5 - Non-Urgent:    Can wait without risk (e.g., minor cut)

This module only covers Level 1 and Level 2, the most critical categories.
"""


# =============================================================================
# CRITICAL RULES - CTAS Level 1 (Resuscitation) & Level 2 (Emergent)
# =============================================================================
# Each rule defines an emergency pattern. Rules are ordered by severity:
# all Level 1 rules come first, then Level 2, so the most dangerous
# conditions are always checked first.
#
# match_type:
#   "any"  — ANY single keyword from the symptoms list triggers the rule
#   "all"  — ALL keywords must be present to trigger the rule
# =============================================================================

CRITICAL_RULES = [
    # -----------------------------------------------------------------
    # CTAS LEVEL 1 — RESUSCITATION (immediate life threat)
    # -----------------------------------------------------------------
    {
        "name": "Cardiac Arrest / Heart Attack",
        "symptoms": ["chest pain", "shortness of breath"],
        "match_type": "all",
        "ctas_level": 1,
        "action": "CALL 911 IMMEDIATELY",
        "description": (
            "Chest pain combined with shortness of breath may indicate a "
            "heart attack or cardiac event requiring immediate emergency care."
        )
    },
    {
        "name": "Stroke (FAST Signs)",
        "symptoms": ["face drooping", "arm weakness", "speech difficulty"],
        "match_type": "all",
        "ctas_level": 1,
        "action": "CALL 911 IMMEDIATELY — Note the time symptoms started",
        "description": (
            "Face drooping, arm weakness, and speech difficulty are classic "
            "FAST signs of stroke. Time is critical — every minute counts."
        )
    },
    {
        "name": "Unconsciousness / Unresponsive",
        "symptoms": ["unconscious", "unresponsive", "passed out", "not breathing"],
        "match_type": "any",
        "ctas_level": 1,
        "action": "CALL 911 IMMEDIATELY — Begin CPR if trained",
        "description": (
            "Unconsciousness or unresponsiveness may indicate cardiac arrest, "
            "stroke, or other life-threatening conditions."
        )
    },
    {
        "name": "Severe Airway Obstruction",
        "symptoms": ["choking", "airway obstruction", "cannot breathe",
                      "unable to breathe"],
        "match_type": "any",
        "ctas_level": 1,
        "action": "CALL 911 IMMEDIATELY — Perform Heimlich maneuver if trained",
        "description": (
            "Complete airway obstruction is immediately life-threatening. "
            "Emergency intervention is required within minutes."
        )
    },
    {
        "name": "Severe Uncontrolled Bleeding",
        "symptoms": ["severe bleeding", "uncontrolled bleeding", "hemorrhage"],
        "match_type": "any",
        "ctas_level": 1,
        "action": "CALL 911 IMMEDIATELY — Apply direct pressure to wound",
        "description": (
            "Severe or uncontrolled bleeding can lead to life-threatening "
            "blood loss within minutes. Apply pressure and call for help."
        )
    },
    {
        "name": "Seizure / Convulsions",
        "symptoms": ["seizure", "convulsions", "convulsing", "fitting"],
        "match_type": "any",
        "ctas_level": 1,
        "action": "CALL 911 IMMEDIATELY — Do not restrain, clear area of hazards",
        "description": (
            "Active seizures require emergency medical response. Protect the "
            "person from injury but do not restrain them or put anything in "
            "their mouth."
        )
    },
    {
        "name": "Poisoning / Overdose",
        "symptoms": ["poisoning", "overdose", "ingested poison", "drug overdose"],
        "match_type": "any",
        "ctas_level": 1,
        "action": "CALL 911 IMMEDIATELY — Call Poison Control: 1-800-567-8911 (BC)",
        "description": (
            "Poisoning or overdose can cause rapid deterioration. Do not "
            "induce vomiting unless directed by Poison Control."
        )
    },

    # -----------------------------------------------------------------
    # CTAS LEVEL 2 — EMERGENT (potential threat to life or limb)
    # -----------------------------------------------------------------
    {
        "name": "Difficulty Breathing",
        "symptoms": ["difficulty breathing", "hard to breathe", "can't breathe",
                      "shortness of breath", "breathing difficulty"],
        "match_type": "any",
        "ctas_level": 2,
        "action": "Go to the nearest Emergency Room or CALL 911",
        "description": (
            "Difficulty breathing on its own can indicate asthma attack, "
            "allergic reaction, pneumonia, or other serious conditions "
            "requiring urgent medical evaluation."
        )
    },
    {
        "name": "Severe Allergic Reaction / Anaphylaxis",
        "symptoms": ["throat swelling", "tongue swelling", "anaphylaxis",
                      "severe allergic reaction", "allergic reaction"],
        "match_type": "any",
        "ctas_level": 2,
        "action": "CALL 911 — Use epinephrine auto-injector (EpiPen) if available",
        "description": (
            "Anaphylaxis can cause airway closure within minutes. Use an "
            "EpiPen immediately if available and call emergency services."
        )
    },
    {
        "name": "Chest Pain",
        "symptoms": ["chest pain", "chest tightness", "chest pressure"],
        "match_type": "any",
        "ctas_level": 2,
        "action": "Go to the nearest Emergency Room or CALL 911",
        "description": (
            "Chest pain alone may indicate a cardiac event, pulmonary "
            "embolism, or other serious condition. Do not ignore chest pain "
            "— seek immediate medical evaluation."
        )
    },
    {
        "name": "Severe Head Injury",
        "symptoms": ["head injury", "head trauma", "hit head", "confusion"],
        "match_type": "any",
        "ctas_level": 2,
        "action": "Go to the nearest Emergency Room — Do not let person sleep",
        "description": (
            "Head injuries with confusion may indicate a concussion or "
            "intracranial bleeding. Medical imaging is often required to "
            "rule out serious damage."
        )
    },
    {
        "name": "Suspected Meningitis",
        "symptoms": ["severe headache", "stiff neck", "light sensitivity"],
        "match_type": "all",
        "ctas_level": 2,
        "action": "Go to the nearest Emergency Room IMMEDIATELY",
        "description": (
            "The combination of severe headache, stiff neck, and light "
            "sensitivity is a classic triad for meningitis, which can be "
            "fatal without rapid treatment."
        )
    },
    {
        "name": "Severe Burns",
        "symptoms": ["severe burn", "major burn", "chemical burn",
                      "electrical burn"],
        "match_type": "any",
        "ctas_level": 2,
        "action": "CALL 911 — Cool burn with running water, do not apply ice",
        "description": (
            "Severe, chemical, or electrical burns require emergency medical "
            "care. Cool with running water for 20 minutes if possible."
        )
    },
    {
        "name": "Mental Health Crisis — Suicidal Thoughts / Self-Harm",
        "symptoms": ["suicidal", "suicidal thoughts", "self-harm",
                      "want to die", "end my life", "kill myself"],
        "match_type": "any",
        "ctas_level": 2,
        "action": (
            "CALL 911 or BC Crisis Line: 1-800-784-2433 (24/7) — "
            "You are not alone, help is available"
        ),
        "description": (
            "Suicidal thoughts and self-harm are a medical emergency. "
            "Immediate support is available through crisis lines and "
            "emergency services. You do not have to face this alone."
        )
    },
]


# =============================================================================
# MAIN FUNCTIONS
# =============================================================================

def check_critical_symptoms(symptoms: list) -> dict:
    """
    Check a list of symptoms against CTAS critical emergency rules.

    This function is the core safety layer. It runs BEFORE any ML model to
    ensure that life-threatening conditions are caught deterministically,
    with no dependence on model accuracy.

    Matching logic:
    - All symptom strings are lowercased for case-insensitive comparison.
    - Keyword matching uses the "in" operator for partial matching, so
      "chest pain on left side" will match the keyword "chest pain".
    - Level 1 rules are checked FIRST (most dangerous), then Level 2.
    - The function returns on the FIRST match (highest severity wins).

    Args:
        symptoms: A list of symptom strings, typically from OpenAI extraction.
                  Example: ["chest pain", "shortness of breath", "dizziness"]

    Returns:
        If a critical rule matches:
            {
                "is_critical": True,
                "rule_name": "Cardiac Arrest / Heart Attack",
                "ctas_level": 1,
                "action": "CALL 911 IMMEDIATELY",
                "description": "...",
                "matched_symptoms": ["chest pain", "shortness of breath"]
            }

        If no rules match:
            {"is_critical": False}
    """
    # Normalize all input symptoms to lowercase for case-insensitive matching
    symptoms_lower = [s.lower() for s in symptoms]

    # Sort rules by CTAS level so Level 1 (most critical) is checked first
    sorted_rules = sorted(CRITICAL_RULES, key=lambda r: r["ctas_level"])

    for rule in sorted_rules:
        matched = []

        # Check each rule keyword against each user symptom
        for keyword in rule["symptoms"]:
            for symptom in symptoms_lower:
                # Partial matching: "chest pain" matches "chest pain on left side"
                if keyword in symptom or symptom in keyword:
                    matched.append(keyword)
                    break  # One match per keyword is enough

        # Determine if the rule triggers based on match_type
        is_triggered = False
        if rule["match_type"] == "any" and len(matched) >= 1:
            is_triggered = True
        elif rule["match_type"] == "all" and len(matched) == len(rule["symptoms"]):
            is_triggered = True

        if is_triggered:
            return {
                "is_critical": True,
                "rule_name": rule["name"],
                "ctas_level": rule["ctas_level"],
                "action": rule["action"],
                "description": rule["description"],
                "matched_symptoms": matched
            }

    # No critical rules matched — safe to proceed to ML classification
    return {"is_critical": False}


def get_all_rules() -> list:
    """
    Return the full list of CTAS critical rules.

    Useful for displaying all monitored emergency patterns in the UI,
    generating documentation, or allowing admins to review the safety layer.

    Returns:
        A list of rule dictionaries, each containing: name, symptoms,
        match_type, ctas_level, action, and description.
    """
    return CRITICAL_RULES
