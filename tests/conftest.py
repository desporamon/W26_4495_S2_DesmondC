"""
Shared pytest fixtures for BC Health Platform test suite.
"""

import os
import sqlite3
import tempfile

import pytest


@pytest.fixture()
def test_db(tmp_path):
    """Create a fresh temporary SQLite test database for each test.

    Yields a (connection, db_path) tuple.  The database file lives in a
    temporary directory and is automatically removed after the test.
    """
    db_path = str(tmp_path / "test_health_platform.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    yield conn, db_path
    conn.close()


@pytest.fixture()
def test_user():
    """Provide a reusable test-user dictionary with standard fields."""
    return {
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "password": "SecurePass123!",
        "age": 34,
        "gender": "Female",
        "health_region": "Vancouver Coastal Health",
    }
