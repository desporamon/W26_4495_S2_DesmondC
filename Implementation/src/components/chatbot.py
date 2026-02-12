# =============================================================================
# BC Health Platform - Chatbot Orchestrator (3-Layer Pipeline)
# =============================================================================
# MEDICAL DISCLAIMER:
# This tool is for informational purposes only and does not replace
# professional medical advice. Always consult a qualified healthcare
# provider for medical concerns. If you are experiencing a medical
# emergency, call 911 immediately.
# =============================================================================

"""
Chatbot orchestrator for the BC Health Platform Symptom Assessment.

This module connects the 3-layer hybrid classification system:
    Layer 1: OpenAI  — Extract structured symptoms from natural language
    Layer 2: Rules   — Catch life-threatening emergencies (CTAS safety layer)
    Layer 3: ML      — Classify non-critical symptoms with a trained model

If the ML model's confidence is below 70%, the system falls back to
OpenAI for general health guidance instead.
"""

import os
import json

import numpy as np
import joblib
import openai
import streamlit as st

from components.openai_utils import extract_symptoms
from components.rules import check_critical_symptoms


# =============================================================================
# PATHS TO TRAINED MODEL FILES
# =============================================================================
# chatbot.py lives in src/components/, model files are in models/
MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "models", "model.pkl"
)
METADATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "models", "model_metadata.json"
)


# =============================================================================
# RECOMMENDATION TEMPLATES BY URGENCY LEVEL
# =============================================================================

RECOMMENDATIONS = {
    "Emergency": (
        "Please call 911 or go to your nearest emergency room immediately."
    ),
    "Urgent": (
        "Please visit a walk-in clinic or urgent care within 24 hours. "
        "If symptoms worsen, call 911."
    ),
    "Routine": (
        "Consider booking an appointment with your family doctor. "
        "Monitor your symptoms."
    ),
    "Self-Care": (
        "This appears to be a minor condition. Rest, stay hydrated, and "
        "use over-the-counter remedies as needed. See a doctor if symptoms "
        "persist beyond 7 days."
    ),
}


# =============================================================================
# MODEL LOADING (cached so it only loads once per session)
# =============================================================================

@st.cache_resource
def load_model():
    """
    Load the trained Random Forest model and its metadata.

    Uses Streamlit's cache_resource so the model is loaded only once
    and shared across all reruns within the same session.

    Returns:
        tuple: (model, metadata_dict)
    """
    model = joblib.load(MODEL_PATH)
    with open(METADATA_PATH, "r") as f:
        metadata = json.load(f)
    return model, metadata


# =============================================================================
# OPENAI FALLBACK GUIDANCE
# =============================================================================

def get_openai_fallback_guidance(symptoms: list, severity: str) -> dict:
    """
    Get general health guidance AND urgency classification from OpenAI
    when ML confidence is too low.

    This is a separate call from symptom extraction — it asks GPT for
    actionable health advice and an urgency level based on the
    already-extracted symptoms.

    Args:
        symptoms: List of symptom strings extracted in Layer 1.
        severity: Severity level string (mild/moderate/severe).

    Returns:
        A dict with keys:
            "recommendation": str — general health guidance text
            "urgency_level":  str — one of Emergency, Urgent, Routine, Self-Care
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.3,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful health assistant for British Columbia, "
                        "Canada. You have two tasks:\n\n"
                        "1. Provide brief, general health guidance based on the "
                        "symptoms described. Include self-care tips and when to "
                        "see a doctor. Keep the guidance under 150 words. Always "
                        "remind the user this is not medical advice.\n\n"
                        "2. Classify the urgency as EXACTLY one of these four "
                        "levels:\n"
                        '  - "Emergency": life-threatening symptoms (chest pain '
                        "with breathing difficulty, stroke signs, severe allergic "
                        "reaction, severe bleeding)\n"
                        '  - "Urgent": needs medical attention within 24 hours '
                        "(high fever, moderate injuries, persistent vomiting, "
                        "severe pain)\n"
                        '  - "Routine": should see a doctor but not immediately '
                        "(mild fever, persistent cough, minor infections, "
                        "ongoing pain)\n"
                        '  - "Self-Care": manageable at home (common cold, mild '
                        "headache, minor allergies, mild stomach ache, skin "
                        "irritation)\n\n"
                        "You MUST respond with ONLY valid JSON in this exact "
                        "format (no extra text):\n"
                        "{\n"
                        '  "urgency_level": "Emergency" or "Urgent" or "Routine" '
                        'or "Self-Care",\n'
                        '  "recommendation": "your guidance text here"\n'
                        "}"
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"I have these symptoms: {', '.join(symptoms)}. "
                        f"Severity: {severity}. What should I do?"
                    )
                }
            ]
        )
        raw = response.choices[0].message.content.strip()
        parsed = json.loads(raw)

        # Validate urgency_level is one of the allowed values
        valid_levels = {"Emergency", "Urgent", "Routine", "Self-Care"}
        urgency = parsed.get("urgency_level", "Routine")
        if urgency not in valid_levels:
            urgency = "Routine"

        return {
            "recommendation": parsed.get("recommendation", raw),
            "urgency_level": urgency,
        }
    except (json.JSONDecodeError, KeyError):
        # OpenAI returned non-JSON — use the raw text as recommendation
        return {
            "recommendation": raw,
            "urgency_level": "Routine",
        }
    except Exception:
        return {
            "recommendation": (
                "Unable to get additional guidance at this time. Please "
                "consult a healthcare provider for your symptoms: "
                f"{', '.join(symptoms)}."
            ),
            "urgency_level": "Routine",
        }


# =============================================================================
# MAIN ASSESSMENT PIPELINE
# =============================================================================

def run_assessment(user_input: str) -> dict:
    """
    Full 3-layer assessment pipeline.

    Flow:
        1. Call extract_symptoms() from openai_utils (Layer 1 — OpenAI)
        2. If error, return error result
        3. Call check_critical_symptoms() from rules (Layer 2 — Rules)
        4. If critical, return emergency result immediately (DO NOT run ML)
        5. If not critical, load ML model and predict (Layer 3 — ML)
        6. Build feature vector using model_metadata.json
        7. Get prediction + confidence via predict_proba()
        8. If confidence >= 0.70, use ML prediction + urgency from metadata
        9. If confidence < 0.70, fall back to OpenAI general guidance
        10. Return complete result dict

    Args:
        user_input: The raw natural-language symptom description from the user.

    Returns:
        dict with keys depending on status:
            "status": "emergency" | "ml_prediction" | "openai_fallback" | "error"
            Plus status-specific fields (see inline comments below).
    """
    # -------------------------------------------------------------------------
    # LAYER 1: OpenAI Symptom Extraction
    # -------------------------------------------------------------------------
    extraction = extract_symptoms(user_input)

    if "error" in extraction:
        return {
            "status": "error",
            "user_input": user_input,
            "error": extraction["error"],
        }

    extracted_symptoms = extraction.get("symptoms", [])
    duration = extraction.get("duration", "unknown")
    severity = extraction.get("severity", "moderate")

    # If no symptoms were extracted, ask the user to elaborate
    if not extracted_symptoms:
        return {
            "status": "error",
            "user_input": user_input,
            "error": (
                "No symptoms could be identified from your description. "
                "Please try again with more detail."
            ),
        }

    # -------------------------------------------------------------------------
    # LAYER 2: CTAS Rule-Based Safety Check
    # -------------------------------------------------------------------------
    critical_result = check_critical_symptoms(extracted_symptoms)

    if critical_result["is_critical"]:
        return {
            "status": "emergency",
            "user_input": user_input,
            "extracted_symptoms": extracted_symptoms,
            "duration": duration,
            "severity": severity,
            "rule_name": critical_result["rule_name"],
            "ctas_level": critical_result["ctas_level"],
            "action": critical_result["action"],
            "description": critical_result["description"],
            "matched_symptoms": critical_result["matched_symptoms"],
        }

    # -------------------------------------------------------------------------
    # LAYER 3: ML Model Prediction
    # -------------------------------------------------------------------------
    try:
        model, metadata = load_model()
        symptom_list = metadata["symptom_list"]
        severity_weights = metadata["severity_weights"]
        urgency_mapping = metadata["urgency_mapping"]
        confidence_threshold = metadata.get("confidence_threshold", 0.70)
        class_names = metadata["class_names"]

        # Build feature vector: zeros array, set matching symptoms to their
        # severity weight from the metadata
        feature_vector = np.zeros(len(symptom_list))

        for symptom in extracted_symptoms:
            # OpenAI returns "chest pain" -> convert to "chest_pain" for lookup
            symptom_key = symptom.lower().strip().replace(" ", "_")
            if symptom_key in symptom_list:
                idx = symptom_list.index(symptom_key)
                feature_vector[idx] = severity_weights.get(symptom_key, 1)

        # Get prediction probabilities
        probas = model.predict_proba(feature_vector.reshape(1, -1))[0]
        max_idx = np.argmax(probas)
        confidence = float(probas[max_idx])
        predicted_disease = class_names[max_idx]

        if confidence >= confidence_threshold:
            # ML prediction is confident enough — use it
            urgency_level = urgency_mapping.get(
                predicted_disease.lower().strip(), "Routine"
            )
            recommendation = RECOMMENDATIONS.get(
                urgency_level, RECOMMENDATIONS["Routine"]
            )

            return {
                "status": "ml_prediction",
                "user_input": user_input,
                "extracted_symptoms": extracted_symptoms,
                "duration": duration,
                "severity": severity,
                "predicted_disease": predicted_disease,
                "confidence": round(confidence, 4),
                "urgency_level": urgency_level,
                "recommendation": recommendation,
            }
        else:
            # Confidence too low — fall back to OpenAI guidance
            fallback = get_openai_fallback_guidance(
                extracted_symptoms, severity
            )

            return {
                "status": "openai_fallback",
                "user_input": user_input,
                "extracted_symptoms": extracted_symptoms,
                "duration": duration,
                "severity": severity,
                "fallback_reason": (
                    f"Model confidence ({confidence:.0%}) below "
                    f"threshold ({confidence_threshold:.0%})"
                ),
                "recommendation": fallback["recommendation"],
                "urgency_level": fallback["urgency_level"],
            }

    except Exception as e:
        # If ML fails entirely, fall back to OpenAI guidance
        fallback = get_openai_fallback_guidance(
            extracted_symptoms, severity
        )

        return {
            "status": "openai_fallback",
            "user_input": user_input,
            "extracted_symptoms": extracted_symptoms,
            "duration": duration,
            "severity": severity,
            "fallback_reason": f"ML model error: {e}",
            "recommendation": fallback["recommendation"],
            "urgency_level": fallback["urgency_level"],
        }
