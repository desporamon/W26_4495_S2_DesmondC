"""
BC Health Platform - Main Application
Sprint 1D: Login/Register Authentication (UI Redesign)

This is the main entry point for the Streamlit application.
It handles user authentication (login/register) and session management.
Redesigned to match UI mockups with centered card-like layout.
"""

import streamlit as st

# Import database functions for user management
from components.database import (
    create_user,
    get_user_by_email,
    verify_user_exists,
    init_db
)

# Import authentication utilities
from components.auth import (
    hash_password,
    verify_password,
    validate_password_strength,
    validate_email
)


# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="BC Health Platform",
    page_icon="🏥",
    layout="wide"
)


# =============================================================================
# CONSTANTS
# =============================================================================

# BC Health Authority Regions (with placeholder option)
BC_HEALTH_AUTHORITIES = [
    "Select your health authority",
    "Fraser Health",
    "Vancouver Coastal Health",
    "Interior Health",
    "Island Health",
    "Northern Health"
]

# Health conditions organized for two-column checkbox layout
# Column 1 conditions
CONDITIONS_COL1 = [
    "Diabetes",
    "High Blood Pressure",
    "Stroke History",
    "Blood Thinners",
    "Chronic Pain"
]

# Column 2 conditions
CONDITIONS_COL2 = [
    "Heart Disease",
    "Asthma",
    "Pregnancy",
    "Weakened Immune System",
    "None of the above"
]


# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

def init_session_state():
    """
    Initialize all session state variables for authentication.

    Session state persists across reruns of the Streamlit app,
    allowing us to track whether a user is logged in.
    """
    # Check if user is authenticated (logged in)
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    # Store the logged-in user's ID (from database)
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None

    # Store the logged-in user's name (for display)
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None

    # Store the logged-in user's email
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None


def logout():
    """
    Log out the current user by resetting all session state variables.
    """
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.user_email = None
    st.rerun()


# =============================================================================
# LOGIN FORM
# =============================================================================

def show_login_form():
    """
    Display the login form matching the UI mockup.

    Features:
    - Email and password inputs
    - Remember me checkbox
    - Forgot password link
    - Demo mode info
    """
    # Create form for login (prevents rerun on every keystroke)
    with st.form(key="login_form"):
        # Email input
        email = st.text_input(
            "Email Address",
            placeholder="Email address",
            label_visibility="collapsed"
        )

        # Password input
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Password",
            label_visibility="collapsed"
        )

        # Remember me checkbox
        remember_me = st.checkbox("Remember me")

        # Login button (full width)
        login_clicked = st.form_submit_button(
            "Login",
            use_container_width=True
        )

        # Handle login submission
        if login_clicked:
            # Validate fields are not empty
            if not email or not password:
                st.error("Please enter both email and password.")
            else:
                # Look up user in database
                user = get_user_by_email(email.strip().lower())

                if user is None:
                    st.error("No account found with this email address.")
                elif verify_password(password, user['password_hash']):
                    # Password correct - log in!
                    st.session_state.authenticated = True
                    st.session_state.user_id = user['id']
                    st.session_state.user_name = user['name']
                    st.session_state.user_email = user['email']
                    st.success(f"Welcome back, {user['name']}!")
                    st.rerun()
                else:
                    st.error("Incorrect password. Please try again.")

    st.divider()

    # Demo mode info
    st.info("Demo Mode: Use test@test.com / Password123")


# =============================================================================
# REGISTRATION FORM
# =============================================================================

def show_register_form():
    """
    Display the registration form matching the UI mockup.

    Features:
    - Personal info: name, email, password, confirm password
    - Health profile: age, gender, health authority
    - Health conditions as checkboxes in two columns
    """
    # Create form for registration
    with st.form(key="register_form"):
        # -----------------------------------------
        # Account Information
        # -----------------------------------------

        # Full name input
        name = st.text_input(
            "Full Name",
            placeholder="Full Name",
            label_visibility="collapsed"
        )

        # Email input
        email = st.text_input(
            "Email Address",
            placeholder="Email Address",
            label_visibility="collapsed"
        )

        # Password input
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Password",
            label_visibility="collapsed"
        )

        # Confirm password input
        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            placeholder="Confirm Password",
            label_visibility="collapsed"
        )

        st.divider()

        # -----------------------------------------
        # Health Profile Section
        # -----------------------------------------

        st.markdown("**Health Profile (Recommended)**")
        st.markdown(
            "<p style='font-size: 14px; color: gray; margin-top: -10px;'>"
            "This helps us provide personalized health recommendations"
            "</p>",
            unsafe_allow_html=True
        )

        # Two columns for Age and Gender
        col1, col2 = st.columns(2)

        with col1:
            age = st.number_input(
                "Age",
                min_value=1,
                max_value=120,
                value=None,
                placeholder="Your age"
            )

        with col2:
            gender = st.selectbox(
                "Gender",
                options=["Select gender", "Male", "Female", "Other", "Prefer not to say"]
            )

        # BC Health Authority dropdown
        health_authority = st.selectbox(
            "BC Health Authority",
            options=BC_HEALTH_AUTHORITIES
        )

        # -----------------------------------------
        # Health Conditions (Checkboxes)
        # -----------------------------------------

        st.write("**Existing Conditions:**")
        st.caption("Select all that apply")

        # Create two columns for checkboxes
        cond_col1, cond_col2 = st.columns(2)

        # Dictionary to store checkbox states
        conditions_selected = {}

        # Column 1 checkboxes
        with cond_col1:
            for condition in CONDITIONS_COL1:
                conditions_selected[condition] = st.checkbox(condition, key=f"cond_{condition}")

        # Column 2 checkboxes
        with cond_col2:
            for condition in CONDITIONS_COL2:
                conditions_selected[condition] = st.checkbox(condition, key=f"cond_{condition}")

        # Info box about personalization
        st.info("This helps us provide personalized health recommendations")

        # Create Account button (full width)
        register_clicked = st.form_submit_button(
            "Create Account",
            use_container_width=True
        )

        # Handle registration submission
        if register_clicked:
            # -----------------------------------------
            # Validation Checks
            # -----------------------------------------

            # Check required fields
            if not name or not email or not password or not confirm_password:
                st.error("Please fill in all required fields.")

            # Validate email format
            elif not validate_email(email.strip())[0]:
                email_valid, email_message = validate_email(email.strip())
                st.error(f"Invalid email: {email_message}")

            # Check if email already exists
            elif verify_user_exists(email.strip().lower()):
                st.error("An account with this email already exists. Please login instead.")

            # Validate password strength
            elif not validate_password_strength(password)[0]:
                password_valid, password_message = validate_password_strength(password)
                st.error(f"Weak password: {password_message}")

            # Check passwords match
            elif password != confirm_password:
                st.error("Passwords do not match. Please try again.")

            else:
                # -----------------------------------------
                # Create the User Account
                # -----------------------------------------

                # Hash password for secure storage
                hashed_password = hash_password(password)

                # Clean up optional fields
                clean_gender = gender if gender != "Select gender" else None
                clean_region = health_authority if health_authority != "Select your health authority" else None

                # Collect selected health conditions from checkboxes
                selected_conditions = [
                    condition for condition, is_selected in conditions_selected.items()
                    if is_selected and condition != "None of the above"
                ]

                # If no conditions selected or "None of the above" is selected, set to None
                if not selected_conditions or conditions_selected.get("None of the above", False):
                    selected_conditions = None

                # Create user in database
                user_id = create_user(
                    name=name.strip(),
                    email=email.strip().lower(),
                    password_hash=hashed_password,
                    age=age,
                    gender=clean_gender,
                    region=clean_region,
                    health_conditions=selected_conditions
                )

                if user_id:
                    # Success! Auto-login the new user
                    st.session_state.authenticated = True
                    st.session_state.user_id = user_id
                    st.session_state.user_name = name.strip()
                    st.session_state.user_email = email.strip().lower()

                    st.success(f"Account created successfully! Welcome, {name}!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Failed to create account. Please try again later.")



# =============================================================================
# AUTHENTICATED VIEW (After Login)
# =============================================================================

def show_authenticated_view():
    """
    Display the main app content for logged-in users.

    Shows welcome message in sidebar and main content area.
    """
    # -----------------------------------------
    # Sidebar with user info and logout
    # -----------------------------------------
    with st.sidebar:
        st.markdown(f"### 👤 Welcome, {st.session_state.user_name}")

        st.divider()

        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            logout()

    # -----------------------------------------
    # Main content area
    # -----------------------------------------
    st.title("🏥 BC Health Platform")

    st.success(f"Welcome back, **{st.session_state.user_name}**! 👋")

    st.divider()

    # Quick navigation guide
    st.markdown("""
    ### What would you like to do today?

    Use the sidebar navigation to access different features:

    - 🏠 **Home** - Overview and health tips
    - 💬 **Symptom Assessment** - Get AI-powered health guidance
    - 📊 **My Dashboard** - View your health history
    - 🗺️ **Facility Finder** - Find nearby healthcare facilities
    - 📚 **Health Library** - Browse health information
    - 📈 **System Analytics** - Platform statistics
    """)

    st.divider()

    # User stats placeholder
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label="Assessments", value="0", delta="Start tracking")

    with col2:
        st.metric(label="Health Score", value="--", delta="Complete profile")

    with col3:
        st.metric(label="Days Active", value="1", delta="Welcome!")


# =============================================================================
# UNAUTHENTICATED VIEW (Login/Register)
# =============================================================================

def show_auth_view():
    """
    Display the authentication view with centered card-like layout.

    Uses st.columns([1,2,1]) to center content in the middle column,
    creating a card-like appearance for the login/register forms.
    """
    # Create three columns: left spacer, center content, right spacer
    # Ratio [1,2,1] puts content in the middle with equal spacing
    left_spacer, center_column, right_spacer = st.columns([1, 2, 1])

    with center_column:
        # -----------------------------------------
        # Header Section
        # -----------------------------------------

        # App logo/title (centered)
        st.markdown(
            "<h1 style='text-align: center;'>🏥</h1>",
            unsafe_allow_html=True
        )

        # Create tabs for Login and Register
        login_tab, register_tab = st.tabs(["LOGIN", "REGISTER"])

        # -----------------------------------------
        # Login Tab Content
        # -----------------------------------------
        with login_tab:
            # Title and subtitle (centered)
            st.markdown(
                "<h2 style='text-align: center; margin-bottom: 0;'>Welcome Back</h2>",
                unsafe_allow_html=True
            )
            st.markdown(
                "<p style='text-align: center; color: gray;'>"
                "Sign in to access your health dashboard"
                "</p>",
                unsafe_allow_html=True
            )

            # Show the login form
            show_login_form()

        # -----------------------------------------
        # Register Tab Content
        # -----------------------------------------
        with register_tab:
            # Title and subtitle (centered)
            st.markdown(
                "<h2 style='text-align: center; margin-bottom: 0;'>Create Account</h2>",
                unsafe_allow_html=True
            )
            st.markdown(
                "<p style='text-align: center; color: gray;'>"
                "Join to track your health journey"
                "</p>",
                unsafe_allow_html=True
            )

            # Show the registration form
            show_register_form()

        # -----------------------------------------
        # Footer
        # -----------------------------------------
        st.divider()
        st.markdown(
            "<p style='text-align: center; font-size: 12px; color: gray;'>"
            "© 2026 BC Health Platform | Secure & Confidential"
            "</p>",
            unsafe_allow_html=True
        )


# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    """
    Main application entry point.

    Controls the flow between authentication screens and the main app.
    """
    # Initialize the database (creates tables if they don't exist)
    init_db()

    # Initialize session state variables
    init_session_state()

    # -----------------------------------------
    # Route based on authentication status
    # -----------------------------------------

    if not st.session_state.authenticated:
        # User is NOT logged in - show login/register screens
        show_auth_view()
    else:
        # User IS logged in - show the main app
        show_authenticated_view()


# =============================================================================
# RUN THE APP
# =============================================================================

if __name__ == "__main__":
    main()
