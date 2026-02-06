"""
BC Health Platform - My Dashboard Page
Sprint 1D.7: Page Protection Implementation

This page displays the user's personal health dashboard,
including assessment history, health metrics, and profile info.
"""

import streamlit as st
from components.auth import require_authentication


# =============================================================================
# PAGE PROTECTION - Must be logged in to view this page
# =============================================================================
# This MUST be called BEFORE any other page content!
# If user is not authenticated, they will see a warning and the page stops here.
require_authentication()


# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="My Dashboard - BC Health Platform",
    page_icon="📊",
    layout="wide"
)


# =============================================================================
# PAGE CONTENT (Only visible to authenticated users)
# =============================================================================

# Page header with personalized greeting
st.title("📊 My Dashboard")
st.write(f"Your personal health overview, **{st.session_state.user_name}**")

st.divider()

# -----------------------------------------
# Quick Stats Section
# -----------------------------------------
st.subheader("📈 Your Health Summary")

# Display metrics in columns
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Assessments",
        value="0",
        delta="Start tracking",
        help="Number of symptom assessments you've completed"
    )

with col2:
    st.metric(
        label="This Month",
        value="0",
        delta="No assessments yet",
        help="Assessments completed this month"
    )

with col3:
    st.metric(
        label="Health Score",
        value="--",
        delta="Complete profile",
        help="Your overall health score based on assessments"
    )

with col4:
    st.metric(
        label="Days Active",
        value="1",
        delta="Just started!",
        help="Number of days you've been using the platform"
    )

st.divider()

# -----------------------------------------
# Assessment History Section
# -----------------------------------------
st.subheader("📋 Assessment History")

# Check if user has any assessments (placeholder check)
has_assessments = False  # This will be connected to database in future sprint

if has_assessments:
    # TODO: Display actual assessment history from database
    st.write("Your assessment history will appear here.")
else:
    # No assessments yet - show helpful message
    st.info("""
    📭 **No assessments yet!**

    You haven't completed any symptom assessments.
    Start your first assessment to track your health journey.
    """)

    if st.button("💬 Start Your First Assessment", use_container_width=True):
        st.switch_page("pages/2_💬_Symptom_Assessment.py")

st.divider()

# -----------------------------------------
# Profile Section
# -----------------------------------------
st.subheader("👤 Your Profile")

# Create two columns for profile info
profile_col1, profile_col2 = st.columns(2)

with profile_col1:
    st.markdown("**Account Information**")
    st.write(f"📧 Email: {st.session_state.user_email}")
    st.write(f"👤 Name: {st.session_state.user_name}")

with profile_col2:
    st.markdown("**Health Profile**")
    st.caption("Your health profile helps us provide personalized recommendations.")
    if st.button("✏️ Edit Profile", use_container_width=True):
        st.info("Profile editing will be available in a future update.")

st.divider()

# -----------------------------------------
# Quick Actions
# -----------------------------------------
st.subheader("🚀 Quick Actions")

action_col1, action_col2, action_col3 = st.columns(3)

with action_col1:
    if st.button("💬 New Assessment", use_container_width=True):
        st.switch_page("pages/2_💬_Symptom_Assessment.py")

with action_col2:
    if st.button("🗺️ Find Healthcare", use_container_width=True):
        st.switch_page("pages/4_🗺️_Facility_Finder.py")

with action_col3:
    if st.button("📚 Health Library", use_container_width=True):
        st.switch_page("pages/5_📚_Health_Library.py")


# -----------------------------------------
# Footer
# -----------------------------------------
st.divider()
st.caption("BC Health Platform - Tracking your health journey in British Columbia")
