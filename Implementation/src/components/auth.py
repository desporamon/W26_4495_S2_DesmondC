"""
Authentication Utilities for BC Health Platform
Sprint 1D.1 - Password Hashing and Validation

This module provides secure password hashing using bcrypt and
validation functions for passwords and emails.

bcrypt is a password hashing algorithm designed to be slow and
computationally expensive, making it resistant to brute-force attacks.
"""

import bcrypt
import re


# =============================================================================
# PASSWORD HASHING FUNCTIONS
# =============================================================================

def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.

    bcrypt automatically handles:
    - Generating a random salt (makes each hash unique)
    - Combining the salt with the password
    - Creating a secure hash

    Args:
        password: The plain text password to hash

    Returns:
        str: The hashed password (includes salt, safe to store in database)

    Example:
        >>> hashed = hash_password("mySecurePassword123")
        >>> print(hashed)  # Something like: $2b$12$LQv3c1yqBw...
    """
    # Convert password string to bytes (bcrypt requires bytes)
    password_bytes = password.encode('utf-8')

    # Generate a salt - the "12" in gensalt() is the work factor
    # Higher = more secure but slower (12 is a good default)
    salt = bcrypt.gensalt()

    # Hash the password with the salt
    hashed = bcrypt.hashpw(password_bytes, salt)

    # Convert bytes back to string for storage in database
    return hashed.decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a stored hash.

    bcrypt.checkpw() extracts the salt from the stored hash
    and uses it to hash the provided password, then compares
    the results securely (timing-attack resistant).

    Args:
        password: The plain text password to verify
        hashed_password: The stored bcrypt hash from the database

    Returns:
        bool: True if password matches, False otherwise

    Example:
        >>> hashed = hash_password("myPassword123")
        >>> verify_password("myPassword123", hashed)  # True
        >>> verify_password("wrongPassword", hashed)  # False
    """
    try:
        # Convert both to bytes for bcrypt
        password_bytes = password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')

        # Check if password matches the hash
        return bcrypt.checkpw(password_bytes, hashed_bytes)

    except Exception as e:
        # If anything goes wrong (invalid hash format, etc.), return False
        print(f"Password verification error: {e}")
        return False


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Check if a password meets security requirements.

    Requirements:
    - At least 8 characters long
    - Contains at least one letter (a-z or A-Z)
    - Contains at least one number (0-9)

    Args:
        password: The password to validate

    Returns:
        tuple: (is_valid, message)
            - is_valid: True if password meets all requirements
            - message: Success message or description of what's missing

    Example:
        >>> validate_password_strength("short")
        (False, 'Password must be at least 8 characters long')
        >>> validate_password_strength("SecurePass123")
        (True, 'Password meets all requirements')
    """
    # Check 1: Minimum length
    if len(password) < 8:
        return (False, "Password must be at least 8 characters long")

    # Check 2: Must contain at least one letter
    # re.search() returns None if no match is found
    if not re.search(r'[a-zA-Z]', password):
        return (False, "Password must contain at least one letter")

    # Check 3: Must contain at least one number
    if not re.search(r'[0-9]', password):
        return (False, "Password must contain at least one number")

    # All checks passed!
    return (True, "Password meets all requirements")


def validate_email(email: str) -> tuple[bool, str]:
    """
    Validate basic email format.

    Checks for:
    - Presence of @ symbol
    - Text before the @ (local part)
    - Domain after @ with at least one dot

    Note: This is basic validation. For production apps, consider
    using a library like 'email-validator' for more robust checking.

    Args:
        email: The email address to validate

    Returns:
        tuple: (is_valid, message)
            - is_valid: True if email format is valid
            - message: Success message or description of the issue

    Example:
        >>> validate_email("user@example.com")
        (True, 'Email format is valid')
        >>> validate_email("invalid-email")
        (False, 'Email must contain @ symbol')
    """
    # Remove whitespace
    email = email.strip()

    # Check 1: Must not be empty
    if not email:
        return (False, "Email cannot be empty")

    # Check 2: Must contain @ symbol
    if '@' not in email:
        return (False, "Email must contain @ symbol")

    # Split email into local part and domain
    parts = email.split('@')

    # Check 3: Must have exactly one @ symbol
    if len(parts) != 2:
        return (False, "Email must contain exactly one @ symbol")

    local_part, domain = parts

    # Check 4: Local part (before @) cannot be empty
    if not local_part:
        return (False, "Email must have text before @ symbol")

    # Check 5: Domain must contain at least one dot
    if '.' not in domain:
        return (False, "Email domain must contain a dot (e.g., example.com)")

    # Check 6: Domain cannot start or end with a dot
    if domain.startswith('.') or domain.endswith('.'):
        return (False, "Email domain cannot start or end with a dot")

    # Check 7: Must have text after the last dot (TLD)
    domain_parts = domain.split('.')
    if len(domain_parts[-1]) < 2:
        return (False, "Email must have a valid domain extension")

    # All checks passed!
    return (True, "Email format is valid")


# =============================================================================
# PAGE PROTECTION (Sprint 1D.7)
# =============================================================================

def require_authentication():
    """
    Check if user is authenticated. If not, show warning and stop the page.

    This function should be called at the TOP of every protected page,
    BEFORE any other page content. It acts as a "gate" that prevents
    unauthenticated users from seeing the page content.

    How it works:
    1. Checks if 'authenticated' exists in session_state
    2. If user is NOT authenticated, shows a warning message
    3. Uses st.stop() to halt page rendering (nothing after this runs)

    Usage:
        # At the top of any protected page:
        from components.auth import require_authentication
        require_authentication()

        # Only authenticated users will see content below this line
        st.title("Protected Page")
    """
    import streamlit as st

    # Initialize session state if it doesn't exist yet
    # This handles the case where user navigates directly to a subpage
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    # Check if user is authenticated
    if not st.session_state.authenticated:
        # User is NOT logged in - redirect to the login page
        st.switch_page("app.py")

    # If we reach here, user IS authenticated - page will continue rendering


# =============================================================================
# TEST BLOCK
# =============================================================================

if __name__ == "__main__":
    """
    Test all authentication functions.
    Run this file directly to test: python auth.py
    """
    print("=" * 60)
    print("BC Health Platform - Auth Module Test")
    print("=" * 60)

    # -----------------------------------------
    # Test 1: Password Hashing
    # -----------------------------------------
    print("\n1. Testing hash_password()...")
    test_password = "SecurePassword123"
    hashed = hash_password(test_password)
    print(f"   Original: {test_password}")
    print(f"   Hashed:   {hashed[:50]}...")
    print(f"   Hash length: {len(hashed)} characters")

    # Verify that hashing the same password twice gives different hashes
    # (because each hash uses a different random salt)
    hashed2 = hash_password(test_password)
    print(f"   Same password, different hash: {hashed != hashed2}")

    # -----------------------------------------
    # Test 2: Password Verification
    # -----------------------------------------
    print("\n2. Testing verify_password()...")

    # Test with correct password
    is_valid = verify_password(test_password, hashed)
    print(f"   Correct password verification: {is_valid}")

    # Test with wrong password
    is_valid = verify_password("WrongPassword123", hashed)
    print(f"   Wrong password verification: {is_valid}")

    # Test with case-sensitive password (should fail)
    is_valid = verify_password("securepassword123", hashed)
    print(f"   Case-sensitive check (lowercase): {is_valid}")

    # -----------------------------------------
    # Test 3: Password Strength Validation
    # -----------------------------------------
    print("\n3. Testing validate_password_strength()...")

    test_passwords = [
        ("short", False),           # Too short
        ("abcdefgh", False),        # No numbers
        ("12345678", False),        # No letters
        ("Secure123", True),        # Valid
        ("MyPassword1", True),      # Valid
    ]

    for pwd, expected in test_passwords:
        is_valid, message = validate_password_strength(pwd)
        status = "PASS" if is_valid == expected else "FAIL"
        print(f"   [{status}] '{pwd}' -> {message}")

    # -----------------------------------------
    # Test 4: Email Validation
    # -----------------------------------------
    print("\n4. Testing validate_email()...")

    test_emails = [
        ("user@example.com", True),           # Valid
        ("test.user@domain.co.uk", True),     # Valid with subdomain
        ("name@company.org", True),           # Valid
        ("invalid-email", False),             # No @
        ("user@", False),                     # No domain
        ("@domain.com", False),               # No local part
        ("user@domain", False),               # No dot in domain
        ("user@@domain.com", False),          # Double @
        ("user@.com", False),                 # Domain starts with dot
        ("", False),                          # Empty
    ]

    for email, expected in test_emails:
        is_valid, message = validate_email(email)
        status = "PASS" if is_valid == expected else "FAIL"
        display_email = email if email else "(empty)"
        print(f"   [{status}] '{display_email}' -> {message}")

    # -----------------------------------------
    # Summary
    # -----------------------------------------
    print("\n" + "=" * 60)
    print("Auth module test completed!")
    print("=" * 60)
