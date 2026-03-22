# =============================================================================
# BC Health Platform — CTAS Safety Rules Unit Tests
# =============================================================================
# Sprint 5A: Safety-critical tests for the CTAS rule-based emergency layer.
# Every rule in CRITICAL_RULES must be verified — if these tests fail,
# patients could receive incorrect urgency guidance.
# =============================================================================

import sys
import os
import pytest

# ---------------------------------------------------------------------------
# Path setup — allow imports from Implementation/src/
# ---------------------------------------------------------------------------
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "..", "Implementation", "src"),
)

from components.rules import check_critical_symptoms, CRITICAL_RULES


# ---------------------------------------------------------------------------
# Build parametrize data dynamically from CRITICAL_RULES
# ---------------------------------------------------------------------------
# For each rule we create a test tuple:
#   (rule_name, symptom_input, expected_ctas_level)
#
# "any"  rules  → supply the FIRST keyword only (one is enough)
# "all"  rules  → supply ALL keywords (every one is required)
# ---------------------------------------------------------------------------
POSITIVE_CASES = []
for rule in CRITICAL_RULES:
    if rule["match_type"] == "any":
        symptoms_input = [rule["symptoms"][0]]
    else:  # "all"
        symptoms_input = list(rule["symptoms"])
    POSITIVE_CASES.append(
        pytest.param(
            rule["name"],
            symptoms_input,
            rule["ctas_level"],
            id=rule["name"],
        )
    )


# =============================================================================
# Part 1 — Positive Detection Tests
# =============================================================================
class TestPositiveDetection:
    """Every CTAS rule must correctly flag its symptoms as critical."""

    @pytest.mark.parametrize("rule_name, symptoms, expected_ctas", POSITIVE_CASES)
    def test_rule_triggers_correctly(self, rule_name, symptoms, expected_ctas):
        """Each CTAS rule must detect its matching symptoms and return the
        correct urgency level, rule name, and action guidance."""
        result = check_critical_symptoms(symptoms)

        assert result["is_critical"] is True, (
            f"Rule '{rule_name}' did not trigger for symptoms {symptoms}"
        )
        assert result["ctas_level"] == expected_ctas, (
            f"Expected CTAS level {expected_ctas}, got {result['ctas_level']}"
        )
        assert result["rule_name"] == rule_name
        assert result["action"], "Action string must not be empty"
        assert result["ctas_level"] in (1, 2), (
            "Safety layer must only return Level 1 or Level 2"
        )


# =============================================================================
# Part 2 — Negative Pass-through Tests
# =============================================================================
class TestNegativePassthrough:
    """Non-emergency symptoms must NOT trigger any CTAS rule."""

    def test_nc01_sore_throat(self):
        """NC-01: 'sore throat' alone is not a CTAS Level 1/2 emergency."""
        result = check_critical_symptoms(["sore throat"])
        assert result["is_critical"] is False

    def test_nc02_headache_fatigue(self):
        """NC-02: 'headache' + 'fatigue' should not trigger any rule."""
        result = check_critical_symptoms(["headache", "fatigue"])
        assert result["is_critical"] is False

    def test_nc03_runny_nose_mild_cough(self):
        """NC-03: Common cold symptoms should not trigger any rule."""
        result = check_critical_symptoms(["runny nose", "mild cough"])
        assert result["is_critical"] is False

    def test_nc04_empty_list(self):
        """NC-04: Empty symptom list must not crash and must return safe default."""
        result = check_critical_symptoms([])
        assert result["is_critical"] is False

    def test_nc05_fever_alone(self):
        """NC-05: 'fever' alone is not defined in any CTAS Level 1/2 rule."""
        result = check_critical_symptoms(["fever"])
        assert result["is_critical"] is False


# =============================================================================
# Part 3 — Edge Case Tests
# =============================================================================
class TestEdgeCases:
    """Boundary conditions that must be handled without crashes or false results."""

    def test_ec01_single_exact_keyword(self):
        """EC-01: A single keyword that exactly matches a rule must be detected."""
        result = check_critical_symptoms(["seizure"])
        assert result["is_critical"] is True
        assert result["ctas_level"] == 1

    def test_ec02_mixed_case_input(self):
        """EC-02: Mixed-case input like 'Chest Pain' must still be detected
        because the function lowercases all input before matching."""
        result = check_critical_symptoms(["Chest Pain"])
        assert result["is_critical"] is True
        assert result["ctas_level"] == 2

    def test_ec03_large_non_emergency_list(self):
        """EC-03: A large list of non-emergency symptoms (10+ items) must not
        crash and must return is_critical False."""
        many_symptoms = [
            "sore throat", "runny nose", "mild cough", "fatigue",
            "sneezing", "watery eyes", "earache", "muscle ache",
            "dry skin", "bloating", "hiccups", "dandruff",
        ]
        result = check_critical_symptoms(many_symptoms)
        assert result["is_critical"] is False

    def test_ec04_none_input_does_not_crash(self):
        """EC-04: Passing None must not crash — should return safe default
        or raise a handled error."""
        try:
            result = check_critical_symptoms(None)
            # If the function returns, it must be a safe default
            assert result["is_critical"] is False
        except TypeError:
            # A TypeError is acceptable — None is not iterable
            pass
