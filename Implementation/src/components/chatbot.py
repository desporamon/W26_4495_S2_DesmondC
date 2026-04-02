# =============================================================================
# BC Health Platform - Chatbot Orchestrator (3-Layer Pipeline)
# =============================================================================
# MEDICAL DISCLAIMER:
# This tool is for informational purposes only and does not replace
# professional medical advice. Always consult a qualified healthcare
# provider for medical concerns. If you are experiencing a medical
# emergency, call 911 immediately.
# =============================================================================
# Sprint 3E: Multi-turn chatbot enhancement

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

from components.openai_utils import (
    extract_symptoms,
    extract_symptoms_multiturn,
    generate_follow_up_response,
)
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


# =============================================================================
# MULTI-TURN DIALOG SUPPORT — Sprint 3E
# =============================================================================

# Keywords that indicate pain-related symptoms; used to decide whether to ask
# the body-location follow-up question (only relevant for pain symptoms).
_PAIN_KEYWORDS = {
    "pain", "ache", "aching", "sore", "soreness", "hurt", "hurting",
    "cramp", "cramps", "cramping", "tender", "tenderness", "discomfort",
    "pressure", "tightness",
}


def initialize_dialog_state() -> dict:
    """
    Create and return a fresh multi-turn dialog state dictionary.

    This state is stored in Streamlit's session_state and tracks all
    symptom information gathered across turns of the multi-turn conversation.

    Returns:
        dict: Initial dialog state with empty/null slots and zero counters.
              Keys:
                symptoms           — list of symptom strings accumulated across turns
                duration           — e.g. "3 days", "2 hours", or None
                severity           — e.g. "mild", "moderate", "severe", or None
                body_location      — e.g. "chest", "abdomen", "head", or None
                additional_info    — any other relevant details, or None
                turn_count         — number of user messages received so far
                conversation_history — list of {"role": ..., "content": ...} dicts
                assessment_complete — True once a final assessment has been returned
    """
    return {
        "symptoms": [],
        "duration": None,
        "severity": None,
        "body_location": None,
        "additional_info": None,
        "turn_count": 0,
        "conversation_history": [],
        "assessment_complete": False,
    }


def get_follow_up_question(dialog_state: dict):
    """
    Examine the current dialog state and return the next follow-up question,
    or None if enough information has been collected to trigger a final assessment.

    Slot-filling priority (checked in order):
        1. No symptoms extracted yet → ask user to describe symptoms more clearly.
        2. Symptoms present, no duration → ask how long symptoms have been present.
        3. Symptoms present, no severity → ask for severity rating (1–10 scale).
        4. Symptoms present, no body_location, AND at least one symptom is
           pain-related → ask where the pain is located.
        5. All key slots filled, OR turn_count >= 3 → return None to trigger
           the final assessment pipeline.

    Args:
        dialog_state: The current multi-turn dialog state dictionary.

    Returns:
        str: The next follow-up question to ask the user.
        None: Signals that enough information has been gathered; proceed to
              the final assessment.
    """
    symptoms = dialog_state.get("symptoms", [])
    turn_count = dialog_state.get("turn_count", 0)

    # Hard cap: never ask more than 3 follow-up turns
    if turn_count >= 3:
        return None

    # Slot 1: no symptoms at all — ask for a clearer description
    if not symptoms:
        return (
            "Could you describe your symptoms in a bit more detail? "
            "For example, what exactly are you feeling and where?"
        )

    # Slot 2: always ask severity explicitly on turn 1
    if turn_count == 1:
        return "How severe are your symptoms?"

    # Slot 3: symptoms known, duration missing
    if not dialog_state.get("duration"):
        return "How long have you been experiencing these symptoms?"

    # Slot 4: body location missing and at least one symptom is pain-related
    if not dialog_state.get("body_location"):
        symptoms_text = " ".join(symptoms).lower()
        if any(keyword in symptoms_text for keyword in _PAIN_KEYWORDS):
            return "Where exactly are you feeling this? Can you point to the specific area on your body?"

    # All key slots filled (or no pain to locate) — proceed to assessment
    return None


def _ml_predict(
    extracted_symptoms: list,
    duration: str,
    severity: str,
    user_input: str,
) -> dict:
    """
    Internal helper: run the ML model (Layer 3) on a pre-extracted symptom list.

    Skips Layers 1 and 2 (OpenAI extraction and CTAS check) because the caller
    has already handled those steps. Falls back to OpenAI guidance if ML
    confidence is below the threshold or if the model raises an exception.

    Args:
        extracted_symptoms: List of symptom strings already extracted.
        duration: Duration string (e.g. "3 days") or "unknown".
        severity: Severity string — "mild", "moderate", or "severe".
        user_input: The user's combined input text, stored in the result for
                    the UI to reference.

    Returns:
        dict with "status" of "ml_prediction" or "openai_fallback", plus the
        standard result fields expected by the Symptom Assessment UI.
    """
    try:
        model, metadata = load_model()
        symptom_list = metadata["symptom_list"]
        severity_weights = metadata["severity_weights"]
        urgency_mapping = metadata["urgency_mapping"]
        confidence_threshold = metadata.get("confidence_threshold", 0.70)
        class_names = metadata["class_names"]

        # Build feature vector — same logic as run_assessment()
        feature_vector = np.zeros(len(symptom_list))
        for symptom in extracted_symptoms:
            symptom_key = symptom.lower().strip().replace(" ", "_")
            if symptom_key in symptom_list:
                idx = symptom_list.index(symptom_key)
                feature_vector[idx] = severity_weights.get(symptom_key, 1)

        probas = model.predict_proba(feature_vector.reshape(1, -1))[0]
        max_idx = np.argmax(probas)
        confidence = float(probas[max_idx])
        predicted_disease = class_names[max_idx]

        if confidence >= confidence_threshold:
            urgency_level = urgency_mapping.get(
                predicted_disease.lower().strip(), "Routine"
            )
            recommendation = RECOMMENDATIONS.get(urgency_level, RECOMMENDATIONS["Routine"])
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
            fallback = get_openai_fallback_guidance(extracted_symptoms, severity)
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
        fallback = get_openai_fallback_guidance(extracted_symptoms, severity)
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


def process_multiturn_message(user_input: str, dialog_state: dict) -> dict:
    """
    Orchestrate one turn of the multi-turn chatbot conversation.

    This function drives the slot-filling loop: it extracts symptoms from the
    user's latest message (accumulating across all prior turns), runs the
    mandatory safety check, and either asks a follow-up question or triggers
    the final 3-layer assessment pipeline.

    Turn flow:
        1. Increment turn_count; add user message to conversation_history.
        2. Call extract_symptoms_multiturn() with the current message and the
           full conversation history (minus the just-added turn) so that GPT
           can accumulate all symptoms seen so far.
        3. Merge any new symptoms / duration / severity / body_location into
           dialog_state (de-duplicating symptoms case-insensitively).
        4. CRITICAL SAFETY CHECK — always runs, every turn, no exceptions:
           call check_critical_symptoms() on ALL accumulated symptoms. If any
           critical rule matches, return an emergency result immediately.
        5. Call get_follow_up_question(dialog_state) to decide next action.
        6a. If None (all key slots filled OR turn_count >= 3):
               Run _ml_predict() on the accumulated symptom list.
               Mark assessment_complete = True.
               Return the final assessment result dict.
        6b. If a question string is returned:
               Call generate_follow_up_response() to phrase it naturally.
               Add the assistant reply to conversation_history.
               Return a "follow_up" status result dict.

    Args:
        user_input:   The user's latest message text.
        dialog_state: The current multi-turn dialog state dict (mutated in-place).

    Returns:
        dict with "status" of:
            "follow_up"       — chatbot is asking for more information; caller
                                should display result["response"] to the user.
            "emergency"       — critical symptoms detected; return immediately.
            "ml_prediction"   — final confident ML-based assessment.
            "openai_fallback" — final OpenAI-guided assessment (low ML confidence).
            "error"           — extraction or pipeline failure.
    """
    # Step 1 — advance turn counter and record user message
    dialog_state["turn_count"] += 1
    dialog_state["conversation_history"].append(
        {"role": "user", "content": user_input}
    )

    # Step 2 — extract accumulated symptom data from conversation context
    # Pass history *before* the turn we just appended so GPT sees it as context,
    # not as the message to analyse (we pass user_input separately).
    prior_history = dialog_state["conversation_history"][:-1]
    extraction = extract_symptoms_multiturn(user_input, prior_history)

    if "error" in extraction:
        return {
            "status": "error",
            "user_input": user_input,
            "error": extraction["error"],
        }

    # Step 3 — merge extracted data into dialog_state
    for sym in extraction.get("symptoms", []):
        if sym and sym.lower() not in [s.lower() for s in dialog_state["symptoms"]]:
            dialog_state["symptoms"].append(sym)

    extracted_duration = extraction.get("duration")
    if extracted_duration and extracted_duration != "unknown":
        dialog_state["duration"] = extracted_duration

    extracted_severity = extraction.get("severity")
    if extracted_severity:
        dialog_state["severity"] = extracted_severity

    extracted_location = extraction.get("body_location")
    if extracted_location:
        dialog_state["body_location"] = extracted_location

    # Step 4 — CRITICAL SAFETY CHECK (mandatory every turn)
    all_symptoms = dialog_state["symptoms"]
    if all_symptoms:
        critical_result = check_critical_symptoms(all_symptoms)
        if critical_result["is_critical"]:
            dialog_state["assessment_complete"] = True
            return {
                "status": "emergency",
                "user_input": user_input,
                "extracted_symptoms": all_symptoms,
                "duration": dialog_state.get("duration") or "unknown",
                "severity": dialog_state.get("severity") or "moderate",
                "rule_name": critical_result["rule_name"],
                "ctas_level": critical_result["ctas_level"],
                "action": critical_result["action"],
                "description": critical_result["description"],
                "matched_symptoms": critical_result["matched_symptoms"],
            }

    # Step 5 — decide: ask follow-up or proceed to final assessment
    follow_up_question = get_follow_up_question(dialog_state)

    # Step 6a — enough information: run final assessment pipeline
    if follow_up_question is None:
        if not all_symptoms:
            return {
                "status": "error",
                "user_input": user_input,
                "error": (
                    "No symptoms could be identified from our conversation. "
                    "Please describe what you are feeling in more detail."
                ),
            }

        duration = dialog_state.get("duration") or "unknown"
        severity = dialog_state.get("severity") or "moderate"
        result = _ml_predict(all_symptoms, duration, severity, user_input)
        dialog_state["assessment_complete"] = True
        return result

    # Step 6b — more information needed: generate a natural follow-up reply
    follow_up_text = generate_follow_up_response(
        follow_up_question, dialog_state["conversation_history"]
    )
    dialog_state["conversation_history"].append(
        {"role": "assistant", "content": follow_up_text}
    )

    return {
        "status": "follow_up",
        "user_input": user_input,
        "response": follow_up_text,
        "collected_symptoms": list(dialog_state["symptoms"]),
        "turn_count": dialog_state["turn_count"],
    }
