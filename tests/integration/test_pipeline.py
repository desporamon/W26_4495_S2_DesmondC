# =============================================================================
# BC Health Platform — Integration Tests for the 3-Layer Assessment Pipeline
# =============================================================================
# Tests the full run_assessment() pipeline end-to-end:
#   Layer 1: OpenAI symptom extraction  (MOCKED — no real API calls)
#   Layer 2: CTAS rule-based safety     (REAL — pure Python)
#   Layer 3: ML model prediction        (REAL — loads model.pkl)
#
# OpenAI is mocked so tests are free, deterministic, and offline.
# Streamlit is mocked so chatbot.py can be imported outside a running app.
# =============================================================================

import sys
import types
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Streamlit mock — must be installed in sys.modules BEFORE any import of
# chatbot.py or openai_utils.py touches `import streamlit as st`.
# ---------------------------------------------------------------------------
_mock_st = MagicMock()

# st.secrets must behave like a dict so openai_utils.py line 35
# (openai.api_key = st.secrets["OPENAI_API_KEY"]) works at import time.
_mock_st.secrets = {"OPENAI_API_KEY": "test-key-not-real"}

# st.cache_resource must be a passthrough decorator so load_model()
# is defined as a normal function (no Streamlit caching layer).
_mock_st.cache_resource = lambda func=None, **kw: func if func else (lambda f: f)

# st.session_state — plain dict is enough for imports.
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
# Valid values used for assertions across multiple tests
# ---------------------------------------------------------------------------
VALID_STATUSES = {"emergency", "ml_prediction", "openai_fallback", "error"}
VALID_URGENCY_LEVELS = {"Self-Care", "Routine", "Urgent", "Emergency"}

# Patch targets — must patch where the name is looked up at call time.
# chatbot.py does `from components.openai_utils import extract_symptoms`,
# so the reference lives in components.chatbot, not components.openai_utils.
PATCH_EXTRACT = "components.chatbot.extract_symptoms"
PATCH_FALLBACK = "components.chatbot.get_openai_fallback_guidance"


# =====================================================================
# Integration Tests — Full 3-Layer Assessment Pipeline
# =====================================================================


class TestAssessmentPipeline:
    """End-to-end integration tests for run_assessment().

    Every test mocks extract_symptoms() (Layer 1 — OpenAI) so no real
    API calls are made.  The CTAS rules (Layer 2) and ML model (Layer 3)
    run against their real implementations.
    """

    # -----------------------------------------------------------------
    # Scenario 1 — Emergency circuit breaker
    # -----------------------------------------------------------------

    def test_tc_pipe_01_emergency_circuit_breaker(self):
        """TC-PIPE-01: Input with emergency symptoms (chest pain +
        shortness of breath) triggers the CTAS circuit breaker.
        Status is 'emergency', ctas_level is 1 or 2, and the ML
        model never runs."""
        mock_extraction = {
            "symptoms": ["chest pain", "shortness of breath"],
            "duration": "1 hour",
            "severity": "severe",
            "raw_response": '{"symptoms":["chest pain","shortness of breath"],'
                            '"duration":"1 hour","severity":"severe"}',
        }

        with patch(PATCH_EXTRACT, return_value=mock_extraction) as mock_ext:
            result = run_assessment(
                "I have chest pain and I can't breathe"
            )

        mock_ext.assert_called_once()

        assert result["status"] == "emergency", (
            f"Expected status 'emergency', got {result['status']!r}"
        )
        assert result["ctas_level"] in (1, 2), (
            f"Expected ctas_level 1 or 2, got {result['ctas_level']!r}"
        )
        assert "rule_name" in result, (
            "Emergency result must include 'rule_name'"
        )
        assert "action" in result, (
            "Emergency result must include 'action'"
        )
        # ML keys should NOT be present — circuit breaker fired before ML
        assert "predicted_disease" not in result, (
            "Emergency result should not contain 'predicted_disease' — "
            "ML should not have run"
        )
        assert "confidence" not in result, (
            "Emergency result should not contain 'confidence' — "
            "ML should not have run"
        )

    # -----------------------------------------------------------------
    # Scenario 2 — ML prediction path
    # -----------------------------------------------------------------

    def test_tc_pipe_02_ml_prediction_path(self):
        """TC-PIPE-02: Clear disease symptoms (UTI — 4 matching symptoms)
        pass through Layer 2 safely, ML confidence is above 70%, and
        status is 'ml_prediction' with a valid urgency level.
        get_openai_fallback_guidance() must NOT be called."""
        mock_extraction = {
            "symptoms": [
                "burning micturition",
                "bladder discomfort",
                "continuous feel of urine",
                "foul smell of urine",
            ],
            "duration": "3 days",
            "severity": "moderate",
            "raw_response": '{"symptoms":["burning micturition",'
                            '"bladder discomfort",'
                            '"continuous feel of urine",'
                            '"foul smell of urine"],'
                            '"duration":"3 days","severity":"moderate"}',
        }

        with (
            patch(PATCH_EXTRACT, return_value=mock_extraction),
            patch(PATCH_FALLBACK) as mock_fallback,
        ):
            result = run_assessment(
                "It burns when I urinate and my bladder feels uncomfortable"
            )

        assert result["status"] == "ml_prediction", (
            f"Expected status 'ml_prediction', got {result['status']!r}"
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
        assert "recommendation" in result, (
            "ml_prediction result must include 'recommendation'"
        )

        # The fallback should NOT have been called — confidence was high
        mock_fallback.assert_not_called(), (
            "get_openai_fallback_guidance() should not be called when "
            "ML confidence is above threshold"
        )

    # -----------------------------------------------------------------
    # Scenario 3 — OpenAI fallback path
    # -----------------------------------------------------------------

    def test_tc_pipe_03_openai_fallback_path(self):
        """TC-PIPE-03: Vague symptoms (single 'headache') pass through
        Layer 2 safely, ML confidence is below 70%, and the system
        falls back to OpenAI guidance with status 'openai_fallback'."""
        mock_extraction = {
            "symptoms": ["headache"],
            "duration": "unknown",
            "severity": "mild",
            "raw_response": '{"symptoms":["headache"],'
                            '"duration":"unknown","severity":"mild"}',
        }

        mock_fallback_return = {
            "recommendation": (
                "For a mild headache, rest in a dark room and stay "
                "hydrated. This is not medical advice."
            ),
            "urgency_level": "Self-Care",
        }

        with (
            patch(PATCH_EXTRACT, return_value=mock_extraction),
            patch(PATCH_FALLBACK, return_value=mock_fallback_return)
                as mock_fb,
        ):
            result = run_assessment("I have a headache")

        assert result["status"] == "openai_fallback", (
            f"Expected status 'openai_fallback', got {result['status']!r}"
        )
        assert "fallback_reason" in result, (
            "openai_fallback result must include 'fallback_reason'"
        )
        assert "recommendation" in result, (
            "openai_fallback result must include 'recommendation'"
        )
        assert result["recommendation"], (
            "Recommendation must not be empty"
        )

        mock_fb.assert_called_once(), (
            "get_openai_fallback_guidance() should be called exactly "
            "once for the low-confidence path"
        )

    # -----------------------------------------------------------------
    # Scenario 4 — Safety invariants
    # -----------------------------------------------------------------

    def test_tc_pipe_04_emergency_always_wins(self):
        """TC-PIPE-04: Emergency symptoms ALWAYS return 'emergency' status
        regardless of what else is in the symptom list.  The CTAS circuit
        breaker cannot be bypassed — ML prediction keys must be absent."""
        # Mix emergency symptoms with non-critical ones
        mock_extraction = {
            "symptoms": [
                "chest pain",
                "shortness of breath",
                "headache",
                "cough",
            ],
            "duration": "30 minutes",
            "severity": "severe",
            "raw_response": '{"symptoms":["chest pain",'
                            '"shortness of breath","headache","cough"],'
                            '"duration":"30 minutes","severity":"severe"}',
        }

        with (
            patch(PATCH_EXTRACT, return_value=mock_extraction),
            patch(PATCH_FALLBACK) as mock_fallback,
        ):
            result = run_assessment(
                "I have chest pain and can't breathe, plus a headache "
                "and cough"
            )

        assert result["status"] == "emergency", (
            f"Emergency symptoms must always produce 'emergency' status, "
            f"got {result['status']!r}"
        )
        # ML path must not have been reached
        assert "predicted_disease" not in result, (
            "Emergency result must not contain ML prediction — "
            "circuit breaker should have fired first"
        )
        assert "confidence" not in result, (
            "Emergency result must not contain confidence score — "
            "ML should not have run"
        )
        # OpenAI fallback must not have been called either
        mock_fallback.assert_not_called(), (
            "get_openai_fallback_guidance() must not be called when "
            "the CTAS circuit breaker fires"
        )

    def test_tc_pipe_05_recommendation_never_empty(self):
        """TC-PIPE-05: Every non-error pipeline response contains a
        non-empty recommendation or action field — the user is never
        left without guidance."""
        test_cases = [
            # Emergency path — guidance is in 'action' and 'description'
            {
                "label": "emergency",
                "extraction": {
                    "symptoms": ["seizure"],
                    "duration": "unknown",
                    "severity": "severe",
                    "raw_response": '{"symptoms":["seizure"],'
                                    '"duration":"unknown",'
                                    '"severity":"severe"}',
                },
                "guidance_key": "action",
            },
            # ML prediction path — guidance is in 'recommendation'
            {
                "label": "ml_prediction",
                "extraction": {
                    "symptoms": [
                        "burning micturition",
                        "bladder discomfort",
                        "continuous feel of urine",
                        "foul smell of urine",
                    ],
                    "duration": "3 days",
                    "severity": "moderate",
                    "raw_response": '{"symptoms":["burning micturition",'
                                    '"bladder discomfort",'
                                    '"continuous feel of urine",'
                                    '"foul smell of urine"],'
                                    '"duration":"3 days",'
                                    '"severity":"moderate"}',
                },
                "guidance_key": "recommendation",
            },
        ]

        for case in test_cases:
            with patch(PATCH_EXTRACT, return_value=case["extraction"]):
                result = run_assessment("test input")

            key = case["guidance_key"]
            assert key in result, (
                f"[{case['label']}] Result must contain '{key}'"
            )
            assert result[key], (
                f"[{case['label']}] '{key}' must not be empty, "
                f"got {result[key]!r}"
            )

    def test_tc_pipe_06_status_always_valid(self):
        """TC-PIPE-06: The response status is always one of the four
        valid values: 'emergency', 'ml_prediction', 'openai_fallback',
        or 'error' — regardless of input."""
        test_cases = [
            # Emergency
            {
                "label": "emergency input",
                "extraction": {
                    "symptoms": ["unconscious"],
                    "duration": "unknown",
                    "severity": "severe",
                    "raw_response": '{"symptoms":["unconscious"],'
                                    '"duration":"unknown",'
                                    '"severity":"severe"}',
                },
            },
            # Confident ML
            {
                "label": "confident ML input",
                "extraction": {
                    "symptoms": [
                        "itching",
                        "skin rash",
                        "nodal skin eruptions",
                        "dischromic patches",
                    ],
                    "duration": "1 week",
                    "severity": "moderate",
                    "raw_response": '{"symptoms":["itching","skin rash",'
                                    '"nodal skin eruptions",'
                                    '"dischromic patches"],'
                                    '"duration":"1 week",'
                                    '"severity":"moderate"}',
                },
            },
            # Vague (likely fallback)
            {
                "label": "vague input",
                "extraction": {
                    "symptoms": ["fatigue"],
                    "duration": "unknown",
                    "severity": "mild",
                    "raw_response": '{"symptoms":["fatigue"],'
                                    '"duration":"unknown",'
                                    '"severity":"mild"}',
                },
            },
            # Error — extraction returned an error
            {
                "label": "extraction error",
                "extraction": {
                    "error": "API rate limit reached.",
                },
            },
        ]

        for case in test_cases:
            fallback_return = {
                "recommendation": "Please consult a healthcare provider.",
                "urgency_level": "Routine",
            }
            with (
                patch(PATCH_EXTRACT, return_value=case["extraction"]),
                patch(PATCH_FALLBACK, return_value=fallback_return),
            ):
                result = run_assessment("test input")

            assert result["status"] in VALID_STATUSES, (
                f"[{case['label']}] Status {result['status']!r} is not "
                f"one of {VALID_STATUSES}"
            )
