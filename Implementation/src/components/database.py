"""
SQLite Database Module for BC Health Platform

This module provides database connectivity and CRUD operations for the
BC Health Platform Streamlit application. It manages user accounts and
symptom assessment records.

Database: data/health_platform.db
Tables: users, assessments
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path


# Database path configuration
DB_DIR = Path(__file__).parent.parent.parent / "data"
DB_PATH = DB_DIR / "health_platform.db"


def get_connection() -> sqlite3.Connection:
    """
    Create and return a database connection.

    Creates the data directory and database file if they don't exist.
    Enables foreign key support and returns rows as dictionaries.

    Returns:
        sqlite3.Connection: Database connection object
    """
    # Ensure data directory exists
    DB_DIR.mkdir(parents=True, exist_ok=True)

    # Create connection with row factory for dict-like access
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # Enable foreign key support
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


def init_db() -> None:
    """
    Initialize the database by creating all required tables.

    Creates the users and assessments tables if they don't exist.
    This function is idempotent and safe to call multiple times.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Create users table
        cursor.execute("""
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

        # Create assessments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                symptoms TEXT NOT NULL,
                extracted_symptoms TEXT,
                urgency_level TEXT,
                recommendation TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # Create index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_assessments_user_id
            ON assessments(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_email
            ON users(email)
        """)

        conn.commit()
        print("Database initialized successfully.")

    except sqlite3.Error as e:
        print(f"Error initializing database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


# =============================================================================
# USER CRUD FUNCTIONS
# =============================================================================

def create_user(
    name: str,
    email: str,
    password_hash: str,
    age: Optional[int] = None,
    gender: Optional[str] = None,
    region: Optional[str] = None,
    health_conditions: Optional[List[str]] = None
) -> Optional[int]:
    """
    Create a new user in the database.

    Args:
        name: User's full name
        email: User's email address (must be unique)
        password_hash: Hashed password (never store plain text!)
        age: User's age (optional)
        gender: User's gender (optional)
        region: BC region - Lower Mainland, Vancouver Island, Interior, Northern BC
        health_conditions: List of health conditions (stored as JSON)

    Returns:
        int: The new user's ID, or None if creation failed
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Convert health conditions list to JSON string
    conditions_json = json.dumps(health_conditions) if health_conditions else None

    try:
        cursor.execute("""
            INSERT INTO users (name, email, password_hash, age, gender, region, health_conditions)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, email, password_hash, age, gender, region, conditions_json))

        conn.commit()
        user_id = cursor.lastrowid
        return user_id

    except sqlite3.IntegrityError as e:
        # Email already exists
        print(f"Error creating user: {e}")
        return None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a user by their email address.

    Args:
        email: The email address to search for

    Returns:
        dict: User data dictionary, or None if not found
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()

        if row:
            user = dict(row)
            # Parse health_conditions JSON back to list
            if user.get('health_conditions'):
                user['health_conditions'] = json.loads(user['health_conditions'])
            return user
        return None

    except sqlite3.Error as e:
        print(f"Error fetching user: {e}")
        return None
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve a user by their ID.

    Args:
        user_id: The user's database ID

    Returns:
        dict: User data dictionary, or None if not found
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()

        if row:
            user = dict(row)
            # Parse health_conditions JSON back to list
            if user.get('health_conditions'):
                user['health_conditions'] = json.loads(user['health_conditions'])
            return user
        return None

    except sqlite3.Error as e:
        print(f"Error fetching user: {e}")
        return None
    finally:
        conn.close()


def update_user(user_id: int, **kwargs) -> bool:
    """
    Update user information.

    Args:
        user_id: The user's database ID
        **kwargs: Fields to update (name, email, password_hash, age, gender, region, health_conditions)

    Returns:
        bool: True if update successful, False otherwise
    """
    if not kwargs:
        return False

    conn = get_connection()
    cursor = conn.cursor()

    # Handle health_conditions specially (convert to JSON)
    if 'health_conditions' in kwargs and isinstance(kwargs['health_conditions'], list):
        kwargs['health_conditions'] = json.dumps(kwargs['health_conditions'])

    # Build dynamic UPDATE query
    allowed_fields = {'name', 'email', 'password_hash', 'age', 'gender', 'region', 'health_conditions'}
    update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}

    if not update_fields:
        return False

    set_clause = ", ".join([f"{field} = ?" for field in update_fields.keys()])
    values = list(update_fields.values()) + [user_id]

    try:
        cursor.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
        conn.commit()
        return cursor.rowcount > 0

    except sqlite3.IntegrityError as e:
        print(f"Error updating user (integrity): {e}")
        return False
    except sqlite3.Error as e:
        print(f"Error updating user: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def verify_user_exists(email: str) -> bool:
    """
    Check if a user with the given email exists.

    Args:
        email: The email address to check

    Returns:
        bool: True if user exists, False otherwise
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT 1 FROM users WHERE email = ?", (email,))
        return cursor.fetchone() is not None

    except sqlite3.Error as e:
        print(f"Error checking user existence: {e}")
        return False
    finally:
        conn.close()


# =============================================================================
# ASSESSMENT CRUD FUNCTIONS
# =============================================================================

def save_assessment(
    user_id: int,
    symptoms: str,
    extracted_symptoms: Optional[List[str]] = None,
    urgency_level: Optional[str] = None,
    recommendation: Optional[str] = None
) -> Optional[int]:
    """
    Save a new symptom assessment to the database.

    Args:
        user_id: The ID of the user this assessment belongs to
        symptoms: The user's original symptom description
        extracted_symptoms: List of symptoms extracted by OpenAI (stored as JSON)
        urgency_level: Emergency, Urgent, Routine, or Self-Care
        recommendation: The recommendation given to the user

    Returns:
        int: The new assessment's ID, or None if save failed
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Convert extracted symptoms list to JSON
    symptoms_json = json.dumps(extracted_symptoms) if extracted_symptoms else None

    try:
        cursor.execute("""
            INSERT INTO assessments (user_id, symptoms, extracted_symptoms, urgency_level, recommendation)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, symptoms, symptoms_json, urgency_level, recommendation))

        conn.commit()
        return cursor.lastrowid

    except sqlite3.Error as e:
        print(f"Error saving assessment: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def get_user_assessments(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get a user's assessment history.

    Args:
        user_id: The user's database ID
        limit: Maximum number of assessments to return (default 10)

    Returns:
        list: List of assessment dictionaries, ordered by most recent first
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT * FROM assessments
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user_id, limit))

        rows = cursor.fetchall()
        assessments = []

        for row in rows:
            assessment = dict(row)
            # Parse extracted_symptoms JSON back to list
            if assessment.get('extracted_symptoms'):
                assessment['extracted_symptoms'] = json.loads(assessment['extracted_symptoms'])
            assessments.append(assessment)

        return assessments

    except sqlite3.Error as e:
        print(f"Error fetching assessments: {e}")
        return []
    finally:
        conn.close()


def get_assessment_by_id(assessment_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve a specific assessment by its ID.

    Args:
        assessment_id: The assessment's database ID

    Returns:
        dict: Assessment data dictionary, or None if not found
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM assessments WHERE id = ?", (assessment_id,))
        row = cursor.fetchone()

        if row:
            assessment = dict(row)
            # Parse extracted_symptoms JSON back to list
            if assessment.get('extracted_symptoms'):
                assessment['extracted_symptoms'] = json.loads(assessment['extracted_symptoms'])
            return assessment
        return None

    except sqlite3.Error as e:
        print(f"Error fetching assessment: {e}")
        return None
    finally:
        conn.close()


def get_assessment_stats(user_id: int) -> Dict[str, Any]:
    """
    Get statistics about a user's assessments.

    Args:
        user_id: The user's database ID

    Returns:
        dict: Statistics including:
            - total_count: Total number of assessments
            - most_common_symptom: Most frequently extracted symptom
            - urgency_distribution: Count of each urgency level
    """
    conn = get_connection()
    cursor = conn.cursor()

    stats = {
        'total_count': 0,
        'most_common_symptom': None,
        'urgency_distribution': {
            'Emergency': 0,
            'Urgent': 0,
            'Routine': 0,
            'Self-Care': 0
        }
    }

    try:
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM assessments WHERE user_id = ?", (user_id,))
        stats['total_count'] = cursor.fetchone()[0]

        if stats['total_count'] == 0:
            return stats

        # Get urgency distribution
        cursor.execute("""
            SELECT urgency_level, COUNT(*) as count
            FROM assessments
            WHERE user_id = ? AND urgency_level IS NOT NULL
            GROUP BY urgency_level
        """, (user_id,))

        for row in cursor.fetchall():
            level = row['urgency_level']
            if level in stats['urgency_distribution']:
                stats['urgency_distribution'][level] = row['count']

        # Get most common symptom from extracted symptoms
        cursor.execute("""
            SELECT extracted_symptoms
            FROM assessments
            WHERE user_id = ? AND extracted_symptoms IS NOT NULL
        """, (user_id,))

        symptom_counts = {}
        for row in cursor.fetchall():
            symptoms = json.loads(row['extracted_symptoms'])
            for symptom in symptoms:
                symptom_lower = symptom.lower()
                symptom_counts[symptom_lower] = symptom_counts.get(symptom_lower, 0) + 1

        if symptom_counts:
            stats['most_common_symptom'] = max(symptom_counts, key=symptom_counts.get)

        return stats

    except sqlite3.Error as e:
        print(f"Error calculating stats: {e}")
        return stats
    finally:
        conn.close()


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def delete_user(user_id: int) -> bool:
    """
    Delete a user and all their assessments (cascading delete).

    Args:
        user_id: The user's database ID

    Returns:
        bool: True if deletion successful, False otherwise
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount > 0

    except sqlite3.Error as e:
        print(f"Error deleting user: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def get_all_users_count() -> int:
    """
    Get the total number of registered users.

    Returns:
        int: Total user count
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM users")
        return cursor.fetchone()[0]
    except sqlite3.Error as e:
        print(f"Error counting users: {e}")
        return 0
    finally:
        conn.close()


def get_all_assessments_count() -> int:
    """
    Get the total number of assessments across all users.

    Returns:
        int: Total assessment count
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM assessments")
        return cursor.fetchone()[0]
    except sqlite3.Error as e:
        print(f"Error counting assessments: {e}")
        return 0
    finally:
        conn.close()


# =============================================================================
# TEST / MAIN BLOCK
# =============================================================================

if __name__ == "__main__":
    """
    Test the database module functionality.
    Run this file directly to test: python database.py
    """
    print("=" * 60)
    print("BC Health Platform - Database Module Test")
    print("=" * 60)

    # Initialize database
    print("\n1. Initializing database...")
    init_db()
    print(f"   Database location: {DB_PATH}")

    # Test user creation
    print("\n2. Testing user creation...")
    test_user_id = create_user(
        name="Test User",
        email="test@example.com",
        password_hash="hashed_password_123",
        age=35,
        gender="Female",
        region="Vancouver Island",
        health_conditions=["Diabetes", "Hypertension"]
    )

    if test_user_id:
        print(f"   Created user with ID: {test_user_id}")
    else:
        print("   User creation failed (may already exist)")
        # Try to get existing user
        existing = get_user_by_email("test@example.com")
        if existing:
            test_user_id = existing['id']
            print(f"   Using existing user with ID: {test_user_id}")

    # Test get user by email
    print("\n3. Testing get_user_by_email...")
    user = get_user_by_email("test@example.com")
    if user:
        print(f"   Found user: {user['name']}")
        print(f"   Region: {user['region']}")
        print(f"   Health conditions: {user['health_conditions']}")

    # Test get user by ID
    print("\n4. Testing get_user_by_id...")
    if test_user_id:
        user = get_user_by_id(test_user_id)
        if user:
            print(f"   Found user by ID: {user['name']}")

    # Test user update
    print("\n5. Testing update_user...")
    if test_user_id:
        success = update_user(test_user_id, age=36, region="Lower Mainland")
        print(f"   Update successful: {success}")
        user = get_user_by_id(test_user_id)
        if user:
            print(f"   Updated age: {user['age']}, region: {user['region']}")

    # Test verify user exists
    print("\n6. Testing verify_user_exists...")
    exists = verify_user_exists("test@example.com")
    print(f"   test@example.com exists: {exists}")
    exists = verify_user_exists("nonexistent@example.com")
    print(f"   nonexistent@example.com exists: {exists}")

    # Test assessment creation
    print("\n7. Testing save_assessment...")
    if test_user_id:
        assessment_id = save_assessment(
            user_id=test_user_id,
            symptoms="I have a severe headache and fever for 2 days",
            extracted_symptoms=["headache", "fever"],
            urgency_level="Urgent",
            recommendation="Consider visiting a walk-in clinic within 24 hours."
        )
        print(f"   Created assessment with ID: {assessment_id}")

        # Create another assessment for stats testing
        save_assessment(
            user_id=test_user_id,
            symptoms="Mild cough and runny nose",
            extracted_symptoms=["cough", "runny nose", "headache"],
            urgency_level="Self-Care",
            recommendation="Rest and hydrate. Monitor symptoms."
        )

    # Test get user assessments
    print("\n8. Testing get_user_assessments...")
    if test_user_id:
        assessments = get_user_assessments(test_user_id, limit=5)
        print(f"   Found {len(assessments)} assessments")
        for a in assessments:
            print(f"   - [{a['urgency_level']}] {a['symptoms'][:40]}...")

    # Test get assessment by ID
    print("\n9. Testing get_assessment_by_id...")
    if assessment_id:
        assessment = get_assessment_by_id(assessment_id)
        if assessment:
            print(f"   Symptoms: {assessment['symptoms']}")
            print(f"   Extracted: {assessment['extracted_symptoms']}")
            print(f"   Urgency: {assessment['urgency_level']}")

    # Test assessment stats
    print("\n10. Testing get_assessment_stats...")
    if test_user_id:
        stats = get_assessment_stats(test_user_id)
        print(f"    Total assessments: {stats['total_count']}")
        print(f"    Most common symptom: {stats['most_common_symptom']}")
        print(f"    Urgency distribution: {stats['urgency_distribution']}")

    # Test counts
    print("\n11. Testing count functions...")
    print(f"    Total users: {get_all_users_count()}")
    print(f"    Total assessments: {get_all_assessments_count()}")

    print("\n" + "=" * 60)
    print("Database module test completed!")
    print("=" * 60)
