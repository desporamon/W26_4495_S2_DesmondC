# =============================================================================
# BC Health Platform — Property-Based Fuzz Tests (Hypothesis)
# =============================================================================
# Generates hundreds of random inputs per test to verify that core functions
# never crash and always uphold their contracts — regardless of what an
# attacker, fuzzer, or confused user throws at them.
# =============================================================================

import sys
import os
import sqlite3
from unittest.mock import patch

import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as hyp_st

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

from components.auth import validate_password_strength, validate_email
from components.rules import check_critical_symptoms
from components.database import create_user, init_db, get_connection


# ---------------------------------------------------------------------------
# Reusable strategies
# ---------------------------------------------------------------------------

# Arbitrary text — includes empty, unicode, special chars, very long strings
any_text = hyp_st.text(min_size=0, max_size=500)

# Passwords that satisfy the REAL rules: 8+ chars, >=1 letter, >=1 digit
valid_password = hyp_st.from_regex(
    r"[a-zA-Z][0-9][a-zA-Z0-9]{6,48}", fullmatch=True
)

# Passwords that are always too short (0–7 chars)
short_password = hyp_st.text(min_size=0, max_size=7)

# Strings that never contain "@"
no_at_text = hyp_st.text(min_size=0, max_size=200).filter(lambda s: "@" not in s)

# Structurally valid emails built from parts that satisfy all 6 checks
# in validate_email():  local@domain.tld  where local non-empty,
# domain non-empty and doesn't start/end with ".", tld is 2+ alpha chars.
valid_email = hyp_st.builds(
    lambda local, domain, tld: f"{local}@{domain}.{tld}",
    local=hyp_st.from_regex(r"[a-z][a-z0-9]{0,15}", fullmatch=True),
    domain=hyp_st.from_regex(r"[a-z][a-z0-9]{1,15}", fullmatch=True),
    tld=hyp_st.from_regex(r"[a-z]{2,6}", fullmatch=True),
)

# Lists of arbitrary strings (for CTAS fuzzing)
any_string_list = hyp_st.lists(
    hyp_st.text(min_size=0, max_size=200), min_size=0, max_size=20
)

# Lists of random non-medical gibberish (no CTAS keywords)
_CTAS_KEYWORDS = {
    "chest pain", "shortness of breath", "face drooping", "arm weakness",
    "speech difficulty", "unconscious", "unresponsive", "passed out",
    "not breathing", "choking", "cannot breathe", "unable to breathe",
    "airway obstruction", "severe bleeding", "uncontrolled bleeding",
    "hemorrhage", "seizure", "convulsions", "convulsing", "fitting",
    "poisoning", "overdose", "ingested poison", "drug overdose",
    "difficulty breathing", "hard to breathe", "can't breathe",
    "breathing difficulty", "throat swelling", "tongue swelling",
    "anaphylaxis", "severe allergic reaction", "allergic reaction",
    "chest tightness", "chest pressure", "head injury", "head trauma",
    "hit head", "confusion", "severe headache", "stiff neck",
    "light sensitivity", "severe burn", "major burn", "chemical burn",
    "electrical burn", "suicidal", "suicidal thoughts", "self-harm",
    "want to die", "end my life", "kill myself",
}


def _is_non_medical(s):
    """Return True if string doesn't match any CTAS keyword."""
    lower = s.lower()
    return not any(kw in lower or lower in kw for kw in _CTAS_KEYWORDS)


non_medical_list = hyp_st.lists(
    hyp_st.from_regex(r"xyzzy[a-z]{0,10}", fullmatch=True),
    min_size=1, max_size=10,
)


# ---------------------------------------------------------------------------
# Patch helper for database fuzzing (same pattern as test_database.py)
# ---------------------------------------------------------------------------
PATCH_TARGET = "components.database.get_connection"


def _make_patched_get_connection(db_path: str):
    """Return a factory that creates connections to the test DB."""
    def _patched():
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    return _patched


# =====================================================================
# PART 1 — Password Validation Fuzzing
# =====================================================================


class TestPasswordFuzzing:
    """Fuzz validate_password_strength() with random inputs."""

    @given(password=any_text)
    @settings(max_examples=100)
    def test_tc_fuzz_01_never_crashes(self, password):
        """TC-FUZZ-01: validate_password_strength() never raises an
        exception on ANY string input — empty, unicode, very long,
        special characters, null bytes, etc."""
        result = validate_password_strength(password)

        assert isinstance(result, tuple), (
            f"Expected a tuple, got {type(result).__name__}"
        )
        assert len(result) == 2, (
            f"Expected a 2-tuple (bool, str), got length {len(result)}"
        )
        assert isinstance(result[0], bool), (
            f"First element should be bool, got {type(result[0]).__name__}"
        )
        assert isinstance(result[1], str), (
            f"Second element should be str, got {type(result[1]).__name__}"
        )

    @given(password=valid_password)
    @settings(max_examples=100)
    def test_tc_fuzz_02_valid_passwords_accepted(self, password):
        """TC-FUZZ-02: Any password with 8+ characters, at least one
        letter [a-zA-Z], and at least one digit [0-9] always returns
        (True, ...).  The function must be consistent for all valid
        inputs."""
        is_valid, message = validate_password_strength(password)

        assert is_valid is True, (
            f"Password {password!r} (len={len(password)}) should be valid "
            f"but got (False, {message!r})"
        )

    @given(password=short_password)
    @settings(max_examples=100)
    def test_tc_fuzz_03_short_passwords_rejected(self, password):
        """TC-FUZZ-03: Any password shorter than 8 characters always
        returns (False, ...).  This length rule must hold for ALL
        short passwords regardless of content."""
        is_valid, message = validate_password_strength(password)

        assert is_valid is False, (
            f"Password {password!r} (len={len(password)}) is < 8 chars "
            f"and should be rejected, but got (True, {message!r})"
        )


# =====================================================================
# PART 2 — Email Validation Fuzzing
# =====================================================================


class TestEmailFuzzing:
    """Fuzz validate_email() with random inputs."""

    @given(email=any_text)
    @settings(max_examples=100)
    def test_tc_fuzz_04_never_crashes(self, email):
        """TC-FUZZ-04: validate_email() never raises an exception on
        ANY string input — random strings, empty string, unicode,
        SQL injection attempts, very long strings."""
        result = validate_email(email)

        assert isinstance(result, tuple), (
            f"Expected a tuple, got {type(result).__name__}"
        )
        assert len(result) == 2, (
            f"Expected a 2-tuple (bool, str), got length {len(result)}"
        )
        assert isinstance(result[0], bool), (
            f"First element should be bool, got {type(result[0]).__name__}"
        )
        assert isinstance(result[1], str), (
            f"Second element should be str, got {type(result[1]).__name__}"
        )

    @given(email=no_at_text)
    @settings(max_examples=100)
    def test_tc_fuzz_05_no_at_always_rejected(self, email):
        """TC-FUZZ-05: Any string without '@' always returns
        (False, ...).  This invariant must hold for all possible
        inputs that lack the @ symbol."""
        is_valid, message = validate_email(email)

        assert is_valid is False, (
            f"Email {email!r} has no '@' and should be rejected, "
            f"but got (True, {message!r})"
        )

    @given(email=valid_email)
    @settings(max_examples=100)
    def test_tc_fuzz_06_valid_emails_accepted(self, email):
        """TC-FUZZ-06: A structurally valid email (local@domain.tld)
        that satisfies all 6 checks in validate_email() always returns
        (True, ...).  The strategy builds emails from parts that
        guarantee: non-empty local, exactly one @, domain with dot,
        domain doesn't start/end with dot, TLD is 2+ chars."""
        is_valid, message = validate_email(email)

        assert is_valid is True, (
            f"Email {email!r} is structurally valid but got "
            f"(False, {message!r})"
        )


# =====================================================================
# PART 3 — CTAS Rules Fuzzing
# =====================================================================


class TestCTASFuzzing:
    """Fuzz check_critical_symptoms() with random inputs."""

    @given(symptoms=any_string_list)
    @settings(max_examples=100)
    def test_tc_fuzz_07_never_crashes(self, symptoms):
        """TC-FUZZ-07: check_critical_symptoms() never raises an
        exception on ANY list of strings — empty lists, unicode
        strings, very long strings, SQL injection strings."""
        result = check_critical_symptoms(symptoms)

        assert isinstance(result, dict), (
            f"Expected a dict, got {type(result).__name__}"
        )
        assert "is_critical" in result, (
            f"Result must contain 'is_critical' key, got keys: "
            f"{list(result.keys())}"
        )

    @given(symptoms=non_medical_list)
    @settings(max_examples=100)
    def test_tc_fuzz_08_garbage_never_triggers_emergency(self, symptoms):
        """TC-FUZZ-08: A list of random non-medical gibberish strings
        ALWAYS returns is_critical=False.  Garbage input must never
        trigger a false emergency that could alarm users."""
        result = check_critical_symptoms(symptoms)

        assert result["is_critical"] is False, (
            f"Non-medical symptoms {symptoms!r} should NOT trigger an "
            f"emergency, but got is_critical=True with rule "
            f"{result.get('rule_name', 'unknown')!r}"
        )

    @given(symptoms=any_string_list)
    @settings(max_examples=100)
    def test_tc_fuzz_09_return_structure_consistent(self, symptoms):
        """TC-FUZZ-09: The return dict always contains 'is_critical'
        at minimum.  When is_critical is True, it must also contain
        'rule_name', 'ctas_level', 'action', 'description', and
        'matched_symptoms'."""
        result = check_critical_symptoms(symptoms)

        assert "is_critical" in result, (
            "Result must always contain 'is_critical' key"
        )
        assert isinstance(result["is_critical"], bool), (
            f"'is_critical' should be bool, got "
            f"{type(result['is_critical']).__name__}"
        )

        if result["is_critical"]:
            required_keys = {
                "rule_name", "ctas_level", "action",
                "description", "matched_symptoms",
            }
            missing = required_keys - result.keys()
            assert not missing, (
                f"When is_critical=True, result is missing keys: {missing}"
            )


# =====================================================================
# PART 4 — Database Fuzzing
# =====================================================================


class TestDatabaseFuzzing:
    """Fuzz create_user() with random text to verify it never corrupts
    the database or raises unhandled exceptions."""

    @given(
        name=hyp_st.text(min_size=1, max_size=100),
        email=hyp_st.text(min_size=1, max_size=100),
        password_hash=hyp_st.text(min_size=1, max_size=200),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_tc_fuzz_10_create_user_never_corrupts(
        self, name, email, password_hash, tmp_path
    ):
        """TC-FUZZ-10: create_user() with arbitrary text for name,
        email, and password_hash never corrupts the database.  It
        either returns an int user_id or None — never raises an
        unhandled exception.

        Uses tmp_path with a unique DB file per generated input to
        avoid unique constraint collisions across examples.  The
        function_scoped_fixture health check is suppressed because
        tmp_path reuse is intentional — each example gets its own
        DB file via uuid."""
        import uuid

        db_path = str(tmp_path / f"fuzz_{uuid.uuid4().hex}.db")

        with patch(PATCH_TARGET, _make_patched_get_connection(db_path)):
            init_db()
            result = create_user(
                name=name,
                email=email,
                password_hash=password_hash,
            )

        assert result is None or isinstance(result, int), (
            f"create_user should return int or None, got "
            f"{type(result).__name__}: {result!r}"
        )
