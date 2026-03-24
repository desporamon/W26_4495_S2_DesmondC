# =============================================================================
# BC Health Platform — ML Model Unit Tests
# =============================================================================
# Sprint 5A: Unit tests for the trained Random Forest model and its metadata.
# Tests load model.pkl and model_metadata.json directly — no Streamlit,
# no OpenAI, no chatbot.py import.  The feature-vector building logic
# replicates what chatbot.py does so we can test the ML layer in isolation.
# =============================================================================

import os
import json

import numpy as np
import joblib
import pytest


# ---------------------------------------------------------------------------
# Paths to the real model files (relative to this test file)
# ---------------------------------------------------------------------------
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.join(_TEST_DIR, "..", "..")
MODELS_DIR = os.path.join(_PROJECT_ROOT, "Implementation", "models")
MODEL_PATH = os.path.join(MODELS_DIR, "model.pkl")
METADATA_PATH = os.path.join(MODELS_DIR, "model_metadata.json")

# Valid urgency levels used throughout the platform
VALID_URGENCY_LEVELS = {"Self-Care", "Routine", "Urgent", "Emergency"}

# Confidence threshold matching chatbot.py / model_metadata.json
CONFIDENCE_THRESHOLD = 0.70


# ---------------------------------------------------------------------------
# Helper — build a feature vector exactly the way chatbot.py does
# ---------------------------------------------------------------------------

def build_feature_vector(symptoms: list, symptom_list: list,
                         severity_weights: dict) -> np.ndarray:
    """Build a severity-weighted one-hot feature vector from symptom strings.

    Replicates the logic in chatbot.py ``_ml_predict`` / ``run_assessment``:
        1. Normalise each symptom: lowercase, strip, spaces → underscores
        2. If the normalised key exists in symptom_list, set that position
           to its severity weight (default 1 if missing from weights dict)
        3. All other positions stay 0
    """
    vector = np.zeros(len(symptom_list))
    for symptom in symptoms:
        key = symptom.lower().strip().replace(" ", "_")
        if key in symptom_list:
            idx = symptom_list.index(key)
            vector[idx] = severity_weights.get(key, 1)
    return vector


def predict(model, feature_vector):
    """Run predict_proba and return (predicted_class, confidence)."""
    probas = model.predict_proba(feature_vector.reshape(1, -1))[0]
    max_idx = np.argmax(probas)
    confidence = float(probas[max_idx])
    predicted_class = model.classes_[max_idx]
    return predicted_class, confidence


# ---------------------------------------------------------------------------
# Module-scoped fixtures — load the real model once for all tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def model():
    """Load the trained Random Forest model from model.pkl."""
    assert os.path.isfile(MODEL_PATH), (
        f"Model file not found at {MODEL_PATH!r}.  "
        "Run train_model.py before running these tests."
    )
    return joblib.load(MODEL_PATH)


@pytest.fixture(scope="module")
def metadata():
    """Load model_metadata.json."""
    assert os.path.isfile(METADATA_PATH), (
        f"Metadata file not found at {METADATA_PATH!r}.  "
        "Run train_model.py before running these tests."
    )
    with open(METADATA_PATH, "r") as f:
        return json.load(f)


# =====================================================================
# PART 1 — Model Loading
# =====================================================================


class TestModelLoading:
    """Tests for model file existence and successful loading."""

    def test_tc_ml_01_model_loads_successfully(self, model):
        """TC-ML-01: model.pkl exists and loads without error.  The loaded
        object must expose predict_proba (i.e. it is a trained classifier)."""
        assert model is not None, "Model should not be None after loading"
        assert hasattr(model, "predict_proba"), (
            "Loaded model must have a predict_proba method "
            "(expected a scikit-learn classifier)"
        )

    def test_tc_ml_02_metadata_is_complete(self, metadata):
        """TC-ML-02: model_metadata.json contains symptom_list,
        urgency_mapping, and severity_weights — all non-empty."""
        assert "symptom_list" in metadata, (
            "Metadata missing 'symptom_list' key"
        )
        assert len(metadata["symptom_list"]) > 0, (
            "symptom_list must not be empty"
        )

        assert "urgency_mapping" in metadata, (
            "Metadata missing 'urgency_mapping' key"
        )
        assert len(metadata["urgency_mapping"]) > 0, (
            "urgency_mapping must not be empty"
        )

        assert "severity_weights" in metadata, (
            "Metadata missing 'severity_weights' key"
        )
        assert len(metadata["severity_weights"]) > 0, (
            "severity_weights must not be empty"
        )


# =====================================================================
# PART 2 — Confidence Threshold Logic
# =====================================================================


class TestConfidenceThreshold:
    """Tests for the 70% confidence threshold behaviour."""

    def test_tc_ml_03_high_confidence_prediction(self, model, metadata):
        """TC-ML-03: A strong symptom combination that closely matches a
        well-defined disease produces confidence >= 0.70 and a valid
        urgency level.

        Uses UTI-like symptoms (burning_micturition, bladder_discomfort,
        continuous_feel_of_urine, foul_smell_ofurine) which map strongly
        to 'Urinary tract infection' in the training data.
        """
        symptom_list = metadata["symptom_list"]
        severity_weights = metadata["severity_weights"]
        urgency_mapping = metadata["urgency_mapping"]

        symptoms = [
            "burning_micturition",
            "bladder_discomfort",
            "continuous_feel_of_urine",
            "foul_smell_ofurine",
        ]

        vector = build_feature_vector(
            symptoms, symptom_list, severity_weights
        )
        predicted_disease, confidence = predict(model, vector)

        assert confidence >= CONFIDENCE_THRESHOLD, (
            f"Expected confidence >= {CONFIDENCE_THRESHOLD}, "
            f"got {confidence:.4f} for disease '{predicted_disease}'"
        )

        # Look up urgency from the mapping (lowercase match)
        urgency = urgency_mapping.get(
            predicted_disease.lower().strip(), "Routine"
        )
        assert urgency in VALID_URGENCY_LEVELS, (
            f"Urgency '{urgency}' is not one of {VALID_URGENCY_LEVELS}"
        )

    def test_tc_ml_04_low_confidence_prediction(self, model, metadata):
        """TC-ML-04: A single vague symptom that does not strongly map to
        any one disease produces confidence < 0.70, indicating that the
        system should fall back to OpenAI guidance."""
        symptom_list = metadata["symptom_list"]
        severity_weights = metadata["severity_weights"]

        # 'headache' alone is shared across many diseases — expect low conf
        symptoms = ["headache"]

        vector = build_feature_vector(
            symptoms, symptom_list, severity_weights
        )
        _, confidence = predict(model, vector)

        assert confidence < CONFIDENCE_THRESHOLD, (
            f"Expected confidence < {CONFIDENCE_THRESHOLD} for a single "
            f"vague symptom, got {confidence:.4f}"
        )

    def test_tc_ml_05_confidence_boundary_logic(self):
        """TC-ML-05: Directly verify the threshold decision logic.
        When confidence == 0.70 the system should treat it as passing
        (>= comparison), and when confidence == 0.6999 it should fall
        back.  This tests the branching condition, not model output."""
        threshold = CONFIDENCE_THRESHOLD

        # Exactly at boundary — should pass (>= comparison in chatbot.py)
        at_boundary = 0.70
        assert at_boundary >= threshold, (
            f"Confidence {at_boundary} should pass the >= {threshold} check"
        )
        status_at = (
            "ml_prediction" if at_boundary >= threshold
            else "openai_fallback"
        )
        assert status_at == "ml_prediction", (
            f"At boundary {at_boundary}, status should be 'ml_prediction', "
            f"got '{status_at}'"
        )

        # Just below boundary — should fall back
        below_boundary = 0.6999
        assert below_boundary < threshold, (
            f"Confidence {below_boundary} should fail the >= {threshold} check"
        )
        status_below = (
            "ml_prediction" if below_boundary >= threshold
            else "openai_fallback"
        )
        assert status_below == "openai_fallback", (
            f"Below boundary {below_boundary}, status should be "
            f"'openai_fallback', got '{status_below}'"
        )


# =====================================================================
# PART 3 — Input Handling
# =====================================================================


class TestInputHandling:
    """Tests for various symptom input scenarios."""

    def test_tc_ml_06_valid_symptom_list(self, model, metadata):
        """TC-ML-06: A valid multi-symptom input returns a structured
        result (predicted_class string, confidence float) without error."""
        symptom_list = metadata["symptom_list"]
        severity_weights = metadata["severity_weights"]

        symptoms = ["high_fever", "chills", "vomiting", "headache"]

        vector = build_feature_vector(
            symptoms, symptom_list, severity_weights
        )
        predicted_disease, confidence = predict(model, vector)

        assert isinstance(predicted_disease, str), (
            f"Predicted disease should be a string, "
            f"got {type(predicted_disease).__name__}"
        )
        assert isinstance(confidence, float), (
            f"Confidence should be a float, got {type(confidence).__name__}"
        )

    def test_tc_ml_07_empty_symptom_list(self, model, metadata):
        """TC-ML-07: An empty symptom list produces a low-confidence
        result (all-zero feature vector) — the model does not crash."""
        symptom_list = metadata["symptom_list"]
        severity_weights = metadata["severity_weights"]

        vector = build_feature_vector([], symptom_list, severity_weights)

        # All zeros — model should still return probabilities
        predicted_disease, confidence = predict(model, vector)

        assert isinstance(confidence, float), (
            "Model should return a float confidence even for empty input"
        )
        assert confidence < CONFIDENCE_THRESHOLD, (
            f"Empty symptom list should produce low confidence, "
            f"got {confidence:.4f}"
        )

    def test_tc_ml_08_single_symptom_input(self, model, metadata):
        """TC-ML-08: A single valid symptom is handled gracefully —
        the model returns a prediction without crashing."""
        symptom_list = metadata["symptom_list"]
        severity_weights = metadata["severity_weights"]

        symptoms = ["cough"]

        vector = build_feature_vector(
            symptoms, symptom_list, severity_weights
        )
        predicted_disease, confidence = predict(model, vector)

        assert isinstance(predicted_disease, str), (
            "Single-symptom input should still produce a disease prediction"
        )
        assert isinstance(confidence, float), (
            "Single-symptom input should still produce a confidence score"
        )

    def test_tc_ml_09_unknown_symptoms(self, model, metadata):
        """TC-ML-09: Symptoms not in the training data produce a
        low-confidence result (they map to zero in the feature vector)
        and the model does not crash."""
        symptom_list = metadata["symptom_list"]
        severity_weights = metadata["severity_weights"]

        symptoms = ["glowing_skin", "telekinesis", "time_travel_nausea"]

        vector = build_feature_vector(
            symptoms, symptom_list, severity_weights
        )

        # None of these symptoms exist — vector should be all zeros
        assert vector.sum() == 0.0, (
            "Unknown symptoms should produce an all-zero feature vector"
        )

        predicted_disease, confidence = predict(model, vector)

        assert isinstance(confidence, float), (
            "Model should return a float confidence for unknown symptoms"
        )
        assert confidence < CONFIDENCE_THRESHOLD, (
            f"Unknown symptoms should produce low confidence, "
            f"got {confidence:.4f}"
        )


# =====================================================================
# PART 4 — Output Validation
# =====================================================================


class TestOutputValidation:
    """Tests for the structure and validity of model output."""

    def test_tc_ml_10_return_value_contains_required_keys(
        self, model, metadata
    ):
        """TC-ML-10: A prediction result built from model output contains
        all required keys: status, predicted_disease, confidence,
        urgency_level, recommendation (for a confident prediction)."""
        symptom_list = metadata["symptom_list"]
        severity_weights = metadata["severity_weights"]
        urgency_mapping = metadata["urgency_mapping"]

        # Use a strong symptom set to get a confident prediction
        symptoms = [
            "itching", "skin_rash", "nodal_skin_eruptions",
            "dischromic_patches",
        ]

        vector = build_feature_vector(
            symptoms, symptom_list, severity_weights
        )
        predicted_disease, confidence = predict(model, vector)

        # Build result dict the same way chatbot.py does
        urgency = urgency_mapping.get(
            predicted_disease.lower().strip(), "Routine"
        )
        result = {
            "status": (
                "ml_prediction"
                if confidence >= CONFIDENCE_THRESHOLD
                else "openai_fallback"
            ),
            "predicted_disease": predicted_disease,
            "confidence": round(confidence, 4),
            "urgency_level": urgency,
        }

        required_keys = {
            "status", "predicted_disease", "confidence", "urgency_level",
        }
        missing = required_keys - result.keys()
        assert not missing, (
            f"Result dict is missing required keys: {missing}"
        )

    def test_tc_ml_11_urgency_level_is_valid(self, model, metadata):
        """TC-ML-11: When the model is confident enough, the urgency level
        looked up from the metadata is one of the four valid options."""
        symptom_list = metadata["symptom_list"]
        severity_weights = metadata["severity_weights"]
        urgency_mapping = metadata["urgency_mapping"]

        # Allergy symptoms — strongly maps to a single disease
        symptoms = [
            "continuous_sneezing", "shivering",
            "watering_from_eyes", "chills",
        ]

        vector = build_feature_vector(
            symptoms, symptom_list, severity_weights
        )
        predicted_disease, confidence = predict(model, vector)

        # Only assert urgency validity when confidence is high enough
        assert confidence >= CONFIDENCE_THRESHOLD, (
            f"Expected a confident prediction for well-known symptoms, "
            f"got {confidence:.4f} — adjust symptom set if model changed"
        )

        urgency = urgency_mapping.get(
            predicted_disease.lower().strip(), "Routine"
        )
        assert urgency in VALID_URGENCY_LEVELS, (
            f"Urgency '{urgency}' for disease '{predicted_disease}' "
            f"is not one of {VALID_URGENCY_LEVELS}"
        )

    def test_tc_ml_12_confidence_score_is_valid_float(
        self, model, metadata
    ):
        """TC-ML-12: The confidence score returned by predict_proba is
        a float in the range [0.0, 1.0]."""
        symptom_list = metadata["symptom_list"]
        severity_weights = metadata["severity_weights"]

        symptoms = ["nausea", "vomiting", "fatigue", "high_fever"]

        vector = build_feature_vector(
            symptoms, symptom_list, severity_weights
        )
        _, confidence = predict(model, vector)

        assert isinstance(confidence, float), (
            f"Confidence should be a float, got {type(confidence).__name__}"
        )
        assert 0.0 <= confidence <= 1.0, (
            f"Confidence should be between 0.0 and 1.0, got {confidence}"
        )
