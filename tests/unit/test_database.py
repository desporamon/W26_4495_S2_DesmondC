# =============================================================================
# BC Health Platform — Database Module Unit Tests
# =============================================================================
# Sprint 5A: Unit tests for all CRUD operations in database.py.
# Every test patches get_connection() so the real health_platform.db
# is never touched — all operations hit a temporary SQLite database.
# =============================================================================

import sys
import os
import sqlite3
from unittest.mock import patch

import pytest

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

from components.database import (
    init_db,
    create_user,
    get_user_by_email,
    get_user_by_id,
    save_assessment,
    get_user_assessments,
    get_assessment_by_id,
)

# The patch target — module-level function inside components.database
PATCH_TARGET = "components.database.get_connection"


# ---------------------------------------------------------------------------
# Helper — patched get_connection factory
# ---------------------------------------------------------------------------

def _make_patched_get_connection(db_path: str):
    """Return a function that creates a new connection to the test DB.

    Each call returns a fresh connection (mimicking the real
    get_connection) with row_factory and foreign keys enabled,
    pointed at the temporary test database instead of the real one.
    """
    def _patched():
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    return _patched


# =====================================================================
# PART 1 — User CRUD Operations
# =====================================================================


class TestUserCRUD:
    """Tests for user creation and retrieval in database.py."""

    def test_tc_db_01_create_user_valid(self, test_db):
        """TC-DB-01: Creating a user with valid data returns a truthy
        user id (integer > 0)."""
        _, db_path = test_db

        with patch(PATCH_TARGET, _make_patched_get_connection(db_path)):
            init_db()
            user_id = create_user(
                name="Alice Smith",
                email="alice@example.com",
                password_hash="$2b$12$fakehashfortest1234567890abcdef",
                age=30,
                gender="Female",
                region="Lower Mainland",
                health_conditions=["Asthma"],
            )

        assert user_id, (
            f"Expected a truthy user id after creation, got {user_id!r}"
        )
        assert isinstance(user_id, int), (
            f"User id should be an int, got {type(user_id).__name__}"
        )

    def test_tc_db_02_get_user_by_email_existing(self, test_db):
        """TC-DB-02: Retrieving a user by an existing email returns the
        correct user record as a dict."""
        _, db_path = test_db

        with patch(PATCH_TARGET, _make_patched_get_connection(db_path)):
            init_db()
            create_user(
                name="Bob Jones",
                email="bob@example.com",
                password_hash="$2b$12$fakehashfortest1234567890abcdef",
            )

            user = get_user_by_email("bob@example.com")

        assert user is not None, "Expected a user dict, got None"
        assert user["email"] == "bob@example.com", (
            f"Email mismatch: expected 'bob@example.com', got {user['email']!r}"
        )
        assert user["name"] == "Bob Jones", (
            f"Name mismatch: expected 'Bob Jones', got {user['name']!r}"
        )

    def test_tc_db_03_get_user_by_email_nonexistent(self, test_db):
        """TC-DB-03: Retrieving a user by a non-existent email returns
        None without raising an exception."""
        _, db_path = test_db

        with patch(PATCH_TARGET, _make_patched_get_connection(db_path)):
            init_db()
            user = get_user_by_email("nobody@example.com")

        assert user is None, (
            f"Expected None for non-existent email, got {user!r}"
        )

    def test_tc_db_04_duplicate_email_returns_none(self, test_db):
        """TC-DB-04: Creating a second user with the same email returns
        None (IntegrityError is caught internally)."""
        _, db_path = test_db

        with patch(PATCH_TARGET, _make_patched_get_connection(db_path)):
            init_db()
            create_user(
                name="Carol First",
                email="carol@example.com",
                password_hash="$2b$12$fakehash1",
            )
            duplicate_id = create_user(
                name="Carol Duplicate",
                email="carol@example.com",
                password_hash="$2b$12$fakehash2",
            )

        assert duplicate_id is None, (
            f"Duplicate email should return None, got {duplicate_id!r}"
        )

    def test_tc_db_05_password_stored_as_bcrypt_hash(self, test_db):
        """TC-DB-05: The password_hash stored in the database starts with
        '$2b$' — plain text is never stored."""
        _, db_path = test_db
        bcrypt_hash = "$2b$12$LJ3m4ys3GzWuGxHBMFN8IeQJFkN9r8X.pkBxLG7CE5Hq2EqDkZuHi"

        with patch(PATCH_TARGET, _make_patched_get_connection(db_path)):
            init_db()
            create_user(
                name="Dave Secure",
                email="dave@example.com",
                password_hash=bcrypt_hash,
            )
            user = get_user_by_email("dave@example.com")

        assert user is not None, "User should exist after creation"
        assert user["password_hash"].startswith("$2b$"), (
            f"Stored hash should start with '$2b$', got: "
            f"{user['password_hash'][:10]!r}"
        )
        assert user["password_hash"] == bcrypt_hash, (
            "Stored hash should match the original bcrypt hash exactly"
        )


# =====================================================================
# PART 2 — Assessment CRUD Operations
# =====================================================================


class TestAssessmentCRUD:
    """Tests for assessment save and retrieval in database.py."""

    def test_tc_db_06_save_assessment_valid(self, test_db):
        """TC-DB-06: Saving an assessment with valid data returns a
        truthy assessment id."""
        _, db_path = test_db

        with patch(PATCH_TARGET, _make_patched_get_connection(db_path)):
            init_db()
            user_id = create_user(
                name="Eva Test",
                email="eva@example.com",
                password_hash="$2b$12$fakehash",
            )
            assessment_id = save_assessment(
                user_id=user_id,
                symptoms="Severe headache and dizziness",
                extracted_symptoms=["headache", "dizziness"],
                urgency_level="Urgent",
                recommendation="Visit a walk-in clinic within 24 hours.",
            )

        assert assessment_id, (
            f"Expected a truthy assessment id, got {assessment_id!r}"
        )
        assert isinstance(assessment_id, int), (
            f"Assessment id should be an int, got {type(assessment_id).__name__}"
        )

    def test_tc_db_07_get_assessments_by_user_id(self, test_db):
        """TC-DB-07: Retrieving assessments by user id returns a list
        of assessment dicts for that user."""
        _, db_path = test_db

        with patch(PATCH_TARGET, _make_patched_get_connection(db_path)):
            init_db()
            user_id = create_user(
                name="Frank Test",
                email="frank@example.com",
                password_hash="$2b$12$fakehash",
            )
            save_assessment(
                user_id=user_id,
                symptoms="Cough and fever",
                urgency_level="Routine",
            )
            save_assessment(
                user_id=user_id,
                symptoms="Chest pain",
                urgency_level="Emergency",
            )

            assessments = get_user_assessments(user_id)

        assert isinstance(assessments, list), (
            f"Expected a list, got {type(assessments).__name__}"
        )
        assert len(assessments) == 2, (
            f"Expected 2 assessments, got {len(assessments)}"
        )

    def test_tc_db_08_get_assessments_empty_list(self, test_db):
        """TC-DB-08: Retrieving assessments for a user with none returns
        an empty list, not None or an error."""
        _, db_path = test_db

        with patch(PATCH_TARGET, _make_patched_get_connection(db_path)):
            init_db()
            user_id = create_user(
                name="Grace Empty",
                email="grace@example.com",
                password_hash="$2b$12$fakehash",
            )

            assessments = get_user_assessments(user_id)

        assert assessments == [], (
            f"Expected an empty list, got {assessments!r}"
        )

    def test_tc_db_09_assessment_stores_all_fields(self, test_db):
        """TC-DB-09: A saved assessment stores symptoms, urgency_level,
        and recommendation — all are retrievable via get_assessment_by_id."""
        _, db_path = test_db

        with patch(PATCH_TARGET, _make_patched_get_connection(db_path)):
            init_db()
            user_id = create_user(
                name="Hank Fields",
                email="hank@example.com",
                password_hash="$2b$12$fakehash",
            )
            assessment_id = save_assessment(
                user_id=user_id,
                symptoms="Nausea and vomiting for 3 days",
                extracted_symptoms=["nausea", "vomiting"],
                urgency_level="Routine",
                recommendation="See your family doctor within a few days.",
            )

            assessment = get_assessment_by_id(assessment_id)

        assert assessment is not None, "Assessment should exist after save"
        assert assessment["symptoms"] == "Nausea and vomiting for 3 days", (
            f"Symptoms mismatch: {assessment['symptoms']!r}"
        )
        assert assessment["urgency_level"] == "Routine", (
            f"Urgency mismatch: {assessment['urgency_level']!r}"
        )
        assert assessment["recommendation"] == (
            "See your family doctor within a few days."
        ), f"Recommendation mismatch: {assessment['recommendation']!r}"
        assert assessment["extracted_symptoms"] == ["nausea", "vomiting"], (
            f"Extracted symptoms mismatch: {assessment['extracted_symptoms']!r}"
        )

    def test_tc_db_10_save_assessment_invalid_user_id(self, test_db):
        """TC-DB-10: Saving an assessment with a non-existent user_id
        returns None (FK IntegrityError caught internally)."""
        _, db_path = test_db

        with patch(PATCH_TARGET, _make_patched_get_connection(db_path)):
            init_db()
            result = save_assessment(
                user_id=99999,
                symptoms="Phantom symptoms",
                urgency_level="Routine",
            )

        assert result is None, (
            f"Expected None for invalid user_id, got {result!r}"
        )


# =====================================================================
# PART 3 — Data Integrity
# =====================================================================


class TestDataIntegrity:
    """Tests for cross-user isolation and database initialisation."""

    def test_tc_db_11_user_isolation(self, test_db):
        """TC-DB-11: Two different users have separate assessment records —
        user A cannot see user B's assessments."""
        _, db_path = test_db

        with patch(PATCH_TARGET, _make_patched_get_connection(db_path)):
            init_db()
            user_a = create_user(
                name="User A",
                email="usera@example.com",
                password_hash="$2b$12$fakehash",
            )
            user_b = create_user(
                name="User B",
                email="userb@example.com",
                password_hash="$2b$12$fakehash",
            )

            save_assessment(
                user_id=user_a,
                symptoms="Headache",
                urgency_level="Self-Care",
            )
            save_assessment(
                user_id=user_a,
                symptoms="Sore throat",
                urgency_level="Routine",
            )
            save_assessment(
                user_id=user_b,
                symptoms="Chest pain",
                urgency_level="Emergency",
            )

            assessments_a = get_user_assessments(user_a)
            assessments_b = get_user_assessments(user_b)

        assert len(assessments_a) == 2, (
            f"User A should have 2 assessments, got {len(assessments_a)}"
        )
        assert len(assessments_b) == 1, (
            f"User B should have 1 assessment, got {len(assessments_b)}"
        )

        # Verify no cross-contamination
        for a in assessments_a:
            assert a["user_id"] == user_a, (
                f"User A's assessment has wrong user_id: {a['user_id']}"
            )
        for b in assessments_b:
            assert b["user_id"] == user_b, (
                f"User B's assessment has wrong user_id: {b['user_id']}"
            )

    def test_tc_db_12_database_initialises_tables(self, test_db):
        """TC-DB-12: After calling init_db(), both the 'users' and
        'assessments' tables exist in the database."""
        conn, db_path = test_db

        with patch(PATCH_TARGET, _make_patched_get_connection(db_path)):
            init_db()

        # Query sqlite_master for table names using the fixture connection
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }

        assert "users" in tables, (
            f"'users' table missing after init_db(). Found: {tables}"
        )
        assert "assessments" in tables, (
            f"'assessments' table missing after init_db(). Found: {tables}"
        )
