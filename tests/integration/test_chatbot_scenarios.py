# =============================================================================
# BC Health Platform — Chatbot Clinical Scenario Integration Tests
# =============================================================================
# Tests 6 clinical scenarios through the full run_assessment() pipeline:
#   Layer 1: OpenAI symptom extraction  (MOCKED — no real API calls)
#   Layer 2: CTAS rule-based safety     (REAL — pure Python)
#   Layer 3: ML model prediction        (REAL — loads model.pkl)
#
# Mocking pattern matches test_pipeline.py exactly.
# =============================================================================

import sys
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Streamlit mock — installed in sys.modules BEFORE any import of chatbot.py
# or openai_utils.py so that `import streamlit as st` resolves to our mock.
# ---------------------------------------------------------------------------
_mock_st = MagicMock()
_mock_st.secrets = {"OPENAI_API_KEY": "test-key-not-real"}
_mock_st.cache_resource = lambda func=None, **kw: func if func else (lambda f: f)
_mock_st.session_state = {}
sys.modules["streamlit"] = _mock_st

# ---------------------------------------------------------------------------
# Path setup — allow imports from Implementation/src/
# ---------------------------------------------------------------------------
sys.path.insert(
    0,
    str(
        __import__("pathlib").Path(__file__).resolve().parents[2]
        / "Implementation"
        / "src"
    ),
)

from components.chatbot import run_assessment  # noqa: E402

# ---------------------------------------------------------------------------
# Patch targets — patch where the name is looked up (chatbot's namespace)
# ---------------------------------------------------------------------------
PATCH_EXTRACT = "components.chatbot.extract_symptoms"
PATCH_FALLBACK = "components.chatbot.get_openai_fallback_guidance"

VALID_STATUSES = {"emergency", "ml_prediction", "openai_fallback", "error"}
VALID_URGENCY_LEVELS = {"Self-Care", "Routine", "Urgent", "Emergency"}


# =====================================================================
# Clinical Scenario Integration Tests
# =====================================================================


class TestChatbotScenarios:
    """Six clinical scenarios exercising every path through run_assessment().

    Each test mocks extract_symptoms() (Layer 1) so no OpenAI API calls
    are made.  The CTAS rules (Layer 2) and ML model (Layer 3) run
    against their real implementations.
    """

    # -----------------------------------------------------------------
    # SCENARIO 1 — Emergency: Cardiac symptoms
    # -----------------------------------------------------------------

    def test_tc_scen_01_cardiac_emergency(self):
        """TC-SCEN-01: Chest pain combined with shortness of breath
        triggers the CTAS Level 1 'Cardiac Arrest / Heart Attack' rule.
        The pipeline returns status 'emergency' with ctas_level 1."""
        mock_extraction = {
            "symptoms": ["chest pain", "shortness of breath"],
            "duration": "2 hours",
            "severity": "severe",
            "raw_response": '{"symptoms":["chest pain",'
                            '"shortness of breath"],'
                            '"duration":"2 hours","severity":"severe"}',
        }

        with patch(PATCH_EXTRACT, return_value=mock_extraction):
            result = run_assessment(
                "I have severe chest pain and I can't breathe"
            )

        assert result["status"] == "emergency", (
            f"Expected status 'emergency', got {result['status']!r}"
        )
        assert result["ctas_level"] == 1, (
            f"Cardiac + SOB should be CTAS Level 1, got {result['ctas_level']}"
        )
        assert "cardiac" in result["rule_name"].lower()  \
            or "heart" in result["rule_name"].lower(), (
            f"Rule name should reference cardiac/heart, "
            f"got {result['rule_name']!r}"
        )
        assert "matched_symptoms" in result, (
            "Emergency result must include 'matched_symptoms'"
        )

    # -----------------------------------------------------------------
    # SCENARIO 2 — Emergency: Stroke symptoms
    # -----------------------------------------------------------------

    def test_tc_scen_02_stroke_emergency(self):
        """TC-SCEN-02: Classic FAST stroke signs (face drooping, arm
        weakness, speech difficulty) trigger the CTAS Level 1 'Stroke'
        rule.  The pipeline returns status 'emergency'."""
        mock_extraction = {
            "symptoms": ["face drooping", "arm weakness",
                         "speech difficulty"],
            "duration": "30 minutes",
            "severity": "severe",
            "raw_response": '{"symptoms":["face drooping",'
                            '"arm weakness","speech difficulty"],'
                            '"duration":"30 minutes","severity":"severe"}',
        }

        with patch(PATCH_EXTRACT, return_value=mock_extraction):
            result = run_assessment(
                "My face is drooping, my arm feels weak, and I can't "
                "speak properly"
            )

        assert result["status"] == "emergency", (
            f"Expected status 'emergency', got {result['status']!r}"
        )
        assert result["ctas_level"] == 1, (
            f"Stroke FAST signs should be CTAS Level 1, "
            f"got {result['ctas_level']}"
        )
        assert "stroke" in result["rule_name"].lower(), (
            f"Rule name should reference 'Stroke', "
            f"got {result['rule_name']!r}"
        )

    # -----------------------------------------------------------------
    # SCENARIO 3 — ML Prediction: High confidence disease (UTI)
    # -----------------------------------------------------------------

    def test_tc_scen_03_ml_prediction_uti(self):
        """TC-SCEN-03: Classic UTI symptoms (burning micturition, bladder
        discomfort, continuous feel of urine, foul smell of urine) are
        not critical, so they pass through Layer 2 and reach the ML model.
        The model predicts with >= 70% confidence and returns status
        'ml_prediction' with a valid urgency level.

        Symptom names use space format (e.g. 'burning micturition')
        matching what OpenAI would realistically return.  The feature
        vector builder normalises them to underscore format for lookup.
        """
        mock_extraction = {
            "symptoms": [
                "burning micturition",
                "bladder discomfort",
                "continuous feel of urine",
                "foul smell ofurine",
            ],
            "duration": "3 days",
            "severity": "moderate",
            "raw_response": '{"symptoms":["burning micturition",'
                            '"bladder discomfort",'
                            '"continuous feel of urine",'
                            '"foul smell ofurine"],'
                            '"duration":"3 days","severity":"moderate"}',
        }

        with (
            patch(PATCH_EXTRACT, return_value=mock_extraction),
            patch(PATCH_FALLBACK) as mock_fallback,
        ):
            result = run_assessment(
                "It burns when I urinate and my bladder is uncomfortable"
            )

        assert result["status"] == "ml_prediction", (
            f"Expected status 'ml_prediction', got {result['status']!r}. "
            f"Full result: {result}"
        )
        assert result["confidence"] >= 0.70, (
            f"Expected confidence >= 0.70, got {result['confidence']}"
        )
        assert result["urgency_level"] in VALID_URGENCY_LEVELS, (
            f"Urgency '{result['urgency_level']}' is not valid. "
            f"Expected one of {VALID_URGENCY_LEVELS}"
        )
        assert "predicted_disease" in result, (
            "ml_prediction result must include 'predicted_disease'"
        )
        assert "recommendation" in result and result["recommendation"], (
            "ml_prediction result must include a non-empty 'recommendation'"
        )

        # OpenAI fallback should NOT have been called
        mock_fallback.assert_not_called(), (
            "get_openai_fallback_guidance() should not be called when "
            "ML confidence is above threshold"
        )

    # -----------------------------------------------------------------
    # SCENARIO 4 — OpenAI Fallback: Vague symptoms
    # -----------------------------------------------------------------

    def test_tc_scen_04_openai_fallback_vague(self):
        """TC-SCEN-04: Vague symptoms (headache, fatigue) are not critical,
        but spread across many diseases so ML confidence falls below 70%.
        The pipeline falls back to OpenAI guidance and returns status
        'openai_fallback' with a recommendation."""
        mock_extraction = {
            "symptoms": ["headache", "fatigue"],
            "duration": "1 day",
            "severity": "mild",
            "raw_response": '{"symptoms":["headache","fatigue"],'
                            '"duration":"1 day","severity":"mild"}',
        }

        mock_fallback_return = {
            "recommendation": (
                "Rest and monitor symptoms. "
                "See a doctor if symptoms worsen."
            ),
            "urgency_level": "Routine",
        }

        with (
            patch(PATCH_EXTRACT, return_value=mock_extraction),
            patch(PATCH_FALLBACK, return_value=mock_fallback_return)
                as mock_fb,
        ):
            result = run_assessment("I have a headache and feel tired")

        assert result["status"] == "openai_fallback", (
            f"Expected status 'openai_fallback', got {result['status']!r}"
        )
        assert "fallback_reason" in result, (
            "openai_fallback result must include 'fallback_reason'"
        )
        assert "recommendation" in result and result["recommendation"], (
            "openai_fallback result must include a non-empty recommendation"
        )
        assert result["urgency_level"] in VALID_URGENCY_LEVELS, (
            f"Urgency '{result['urgency_level']}' is not valid"
        )

        mock_fb.assert_called_once(), (
            "get_openai_fallback_guidance() should be called exactly once "
            "for the low-confidence fallback path"
        )

    # -----------------------------------------------------------------
    # SCENARIO 5 — Safety: Emergency always overrides ML
    # -----------------------------------------------------------------

    def test_tc_scen_05_emergency_overrides_ml(self):
        """TC-SCEN-05: When the symptom list contains BOTH emergency
        keywords (chest pain + shortness of breath) AND non-emergency
        symptoms (cough, headache), the CTAS circuit breaker fires
        first and returns 'emergency'.  The ML model never runs —
        no 'predicted_disease' or 'confidence' keys in the result."""
        mock_extraction = {
            "symptoms": [
                "chest pain",
                "shortness of breath",
                "cough",
                "headache",
                "fatigue",
            ],
            "duration": "1 hour",
            "severity": "severe",
            "raw_response": '{"symptoms":["chest pain",'
                            '"shortness of breath","cough",'
                            '"headache","fatigue"],'
                            '"duration":"1 hour","severity":"severe"}',
        }

        with (
            patch(PATCH_EXTRACT, return_value=mock_extraction),
            patch(PATCH_FALLBACK) as mock_fallback,
        ):
            result = run_assessment(
                "I have chest pain and can't breathe, also have a "
                "cough, headache, and I feel very tired"
            )

        assert result["status"] == "emergency", (
            f"Emergency symptoms must always produce 'emergency' status, "
            f"got {result['status']!r}"
        )
        # ML prediction keys must NOT be present
        assert "predicted_disease" not in result, (
            "Emergency result must not contain 'predicted_disease' — "
            "the CTAS circuit breaker should fire before ML runs"
        )
        assert "confidence" not in result, (
            "Emergency result must not contain 'confidence' — "
            "ML should not have run"
        )
        # OpenAI fallback must not have been called either
        mock_fallback.assert_not_called(), (
            "get_openai_fallback_guidance() must not be called when "
            "the CTAS circuit breaker fires"
        )

    # -----------------------------------------------------------------
    # SCENARIO 6 — Edge case: Minimal valid input
    # -----------------------------------------------------------------

    def test_tc_scen_06_single_non_emergency_symptom(self):
        """TC-SCEN-06: A single non-emergency symptom (nausea) does not
        crash the pipeline.  It returns either 'ml_prediction' or
        'openai_fallback' — never 'emergency' — because nausea alone
        does not trigger any CTAS rule."""
        mock_extraction = {
            "symptoms": ["nausea"],
            "duration": "unknown",
            "severity": "moderate",
            "raw_response": '{"symptoms":["nausea"],'
                            '"duration":"unknown","severity":"moderate"}',
        }

        mock_fallback_return = {
            "recommendation": (
                "Stay hydrated and rest. See a doctor if nausea "
                "persists or worsens."
            ),
            "urgency_level": "Self-Care",
        }

        with (
            patch(PATCH_EXTRACT, return_value=mock_extraction),
            patch(PATCH_FALLBACK, return_value=mock_fallback_return),
        ):
            result = run_assessment("I feel nauseous")

        assert result["status"] in ("ml_prediction", "openai_fallback"), (
            f"Single non-emergency symptom should produce 'ml_prediction' "
            f"or 'openai_fallback', got {result['status']!r}"
        )
        assert result["status"] != "emergency", (
            "Nausea alone must not trigger the emergency circuit breaker"
        )
        assert result["status"] != "error", (
            f"Single valid symptom should not produce an error, "
            f"got: {result.get('error', 'N/A')}"
        )
