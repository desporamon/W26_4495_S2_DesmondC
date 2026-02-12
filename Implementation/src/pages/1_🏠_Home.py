"""
BC Health Platform - Home Page
Sprint 1D.7: Page Protection Implementation

This is the main Home page that users see after logging in.
It provides an overview of the platform and health tips.
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
    page_title="Home - BC Health Platform",
    page_icon="🏠",
    layout="wide"
)

from components.header import render_header
render_header()


# =============================================================================
# PAGE CONTENT (Only visible to authenticated users)
# =============================================================================

# Page header with personalized greeting
st.title("🏠 Home")
st.write(f"Welcome back, **{st.session_state.user_name}**! 👋")

st.divider()

# -----------------------------------------
# Health Tips Section
# -----------------------------------------
st.subheader("💡 Today's Health Tips")

# Display health tips in columns
col1, col2 = st.columns(2)

with col1:
    st.info("""
    **Stay Hydrated** 💧

    Drink at least 8 glasses of water daily.
    Proper hydration helps maintain energy levels
    and supports overall health.
    """)

with col2:
    st.info("""
    **Get Moving** 🚶

    Aim for at least 30 minutes of moderate
    physical activity each day. Even a short
    walk can make a difference!
    """)

st.divider()

# -----------------------------------------
# Quick Actions Section
# -----------------------------------------
st.subheader("🚀 Quick Actions")

# Create action buttons in columns
action_col1, action_col2, action_col3 = st.columns(3)

with action_col1:
    if st.button("💬 Start Symptom Check", use_container_width=True):
        st.switch_page("pages/2_💬_Symptom_Assessment.py")

with action_col2:
    if st.button("📊 View My Dashboard", use_container_width=True):
        st.switch_page("pages/3_📊_My_Dashboard.py")

with action_col3:
    if st.button("🗺️ Find Healthcare", use_container_width=True):
        st.switch_page("pages/4_🗺️_Facility_Finder.py")

st.divider()

# -----------------------------------------
# Recent Activity Placeholder
# -----------------------------------------
st.subheader("📋 Recent Activity")

st.caption("Your recent health activities will appear here.")

# Placeholder for when there's no activity yet
st.info("No recent activity. Start by completing a symptom assessment!")


# -----------------------------------------
# Footer
# -----------------------------------------
st.divider()
st.caption("BC Health Platform - Your trusted health companion in British Columbia")
