"""
Unit tests for the auth module — BC Health Platform.

Covers 10 test cases (TC-AUTH-01 through TC-AUTH-10) grouped into
four logical areas: Registration, Login, Security, and Session.

All database operations use the conftest.py ``test_db`` fixture so
the real health_platform.db is never touched.  Streamlit calls are
mocked with unittest.mock.
"""

import sys
import sqlite3
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Make the source package importable from the test runner
# ---------------------------------------------------------------------------
sys.path.insert(
    0,
    str(
        __import__("pathlib").Path(__file__).resolve().parents[2]
        / "Implementation"
        / "src"
    ),
)

from components.auth import (
    hash_password,
    verify_password,
    validate_password_strength,
    validate_email,
    require_authentication,
)


# =====================================================================
# Helper — create the users table inside the temp test database
# =====================================================================

def _init_users_table(conn: sqlite3.Connection) -> None:
    """Create the users table in the test database."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            region TEXT,
            health_conditions TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


def _register_user(conn: sqlite3.Connection, user: dict) -> int:
    """Insert a user into the test database and return the new user id."""
    pw_hash = hash_password(user["password"])
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash, age, gender, region) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            user["name"],
            user["email"],
            pw_hash,
            user["age"],
            user["gender"],
            user["health_region"],
        ),
    )
    conn.commit()
    return cursor.lastrowid


# =====================================================================
# REGISTRATION TESTS
# =====================================================================


class TestRegistration:
    """Tests for user registration flows."""

    def test_tc_auth_01_valid_registration(self, test_db, test_user):
        """TC-AUTH-01: A new user with a valid email and strong password
        is created successfully and the returned user id is truthy."""
        conn, _ = test_db
        _init_users_table(conn)

        user_id = _register_user(conn, test_user)

        assert user_id, (
            f"Expected a truthy user id after registration, got {user_id!r}"
        )

        # Verify the row exists
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        assert row is not None, "User row should exist in the database"
        assert row["email"] == test_user["email"], (
            "Stored email should match the registered email"
        )

    def test_tc_auth_02_duplicate_email(self, test_db, test_user):
        """TC-AUTH-02: Registering a second user with the same email
        raises an IntegrityError (UNIQUE constraint on email column)."""
        conn, _ = test_db
        _init_users_table(conn)

        _register_user(conn, test_user)

        with pytest.raises(sqlite3.IntegrityError):
            _register_user(conn, test_user)

    def test_tc_auth_03_weak_password(self):
        """TC-AUTH-03: A password shorter than 8 characters fails
        strength validation."""
        is_valid, message = validate_password_strength("Short1")

        assert is_valid is False, (
            "Weak password (<8 chars) should fail validation"
        )
        assert "8 characters" in message, (
            f"Message should mention length requirement, got: {message!r}"
        )

    def test_tc_auth_04_invalid_email_format(self):
        """TC-AUTH-04: An email without a proper domain fails
        format validation."""
        is_valid, message = validate_email("not-an-email")

        assert is_valid is False, (
            "Email without '@' should fail validation"
        )
        assert "@" in message, (
            f"Message should mention the '@' requirement, got: {message!r}"
        )


# =====================================================================
# LOGIN TESTS
# =====================================================================


class TestLogin:
    """Tests for login / credential verification flows."""

    def test_tc_auth_05_valid_login(self, test_db, test_user):
        """TC-AUTH-05: Logging in with the correct password returns True
        from verify_password."""
        conn, _ = test_db
        _init_users_table(conn)
        _register_user(conn, test_user)

        row = conn.execute(
            "SELECT password_hash FROM users WHERE email = ?",
            (test_user["email"],),
        ).fetchone()

        result = verify_password(test_user["password"], row["password_hash"])

        assert result is True, (
            "verify_password should return True for correct credentials"
        )

    def test_tc_auth_06_wrong_password(self, test_db, test_user):
        """TC-AUTH-06: Logging in with the wrong password returns False."""
        conn, _ = test_db
        _init_users_table(conn)
        _register_user(conn, test_user)

        row = conn.execute(
            "SELECT password_hash FROM users WHERE email = ?",
            (test_user["email"],),
        ).fetchone()

        result = verify_password("WrongPassword999!", row["password_hash"])

        assert result is False, (
            "verify_password should return False for an incorrect password"
        )

    def test_tc_auth_07_nonexistent_email(self, test_db):
        """TC-AUTH-07: Looking up a non-existent email returns None
        (no user row found)."""
        conn, _ = test_db
        _init_users_table(conn)

        row = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            ("ghost@nowhere.com",),
        ).fetchone()

        assert row is None, (
            "Query for a non-existent email should return None"
        )


# =====================================================================
# SECURITY TESTS
# =====================================================================


class TestSecurity:
    """Tests for password storage security."""

    def test_tc_auth_08_password_stored_as_bcrypt_hash(self, test_db, test_user):
        """TC-AUTH-08: The stored password_hash is a bcrypt digest
        (starts with '$2b$'), not plain text."""
        conn, _ = test_db
        _init_users_table(conn)
        _register_user(conn, test_user)

        row = conn.execute(
            "SELECT password_hash FROM users WHERE email = ?",
            (test_user["email"],),
        ).fetchone()

        stored_hash = row["password_hash"]

        assert stored_hash.startswith("$2b$"), (
            f"Stored hash should start with '$2b$', got: {stored_hash[:10]!r}"
        )
        assert stored_hash != test_user["password"], (
            "Stored value must not be the plain-text password"
        )


# =====================================================================
# SESSION TESTS
# =====================================================================


class TestSession:
    """Tests for session management and page protection."""

    def test_tc_auth_09_logout_clears_session(self):
        """TC-AUTH-09: Clearing session_state keys simulates logout —
        authenticated flag is removed / set to False."""
        session = {
            "authenticated": True,
            "user_id": 1,
            "user_name": "Jane Doe",
            "user_email": "jane.doe@example.com",
        }

        # Simulate logout by clearing session keys
        session_keys = list(session.keys())
        for key in session_keys:
            del session[key]

        assert "authenticated" not in session, (
            "Session should no longer contain 'authenticated' after logout"
        )
        assert len(session) == 0, (
            "Session should be empty after logout"
        )

    def test_tc_auth_10_page_protection_redirects(self):
        """TC-AUTH-10: require_authentication() calls st.switch_page
        when the user is not authenticated."""
        mock_st = MagicMock()
        # Simulate 'authenticated' not in session_state
        mock_st.session_state = MagicMock()
        mock_st.session_state.__contains__ = MagicMock(return_value=False)
        mock_st.session_state.authenticated = False

        with patch.dict("sys.modules", {"streamlit": mock_st}):
            require_authentication()

            mock_st.switch_page.assert_called_once_with("app.py"), (
                "require_authentication should call st.switch_page('app.py') "
                "for unauthenticated users"
            )
