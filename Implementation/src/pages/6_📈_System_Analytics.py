"""
BC Health Platform - System Analytics Page
Sprint 1D.7: Page Protection Implementation

This page displays platform statistics and analytics,
showing usage metrics and system health information.
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
    page_title="System Analytics - BC Health Platform",
    page_icon="📈",
    layout="wide"
)

from components.header import render_header
render_header()


# =============================================================================
# PAGE CONTENT (Only visible to authenticated users)
# =============================================================================

# Page header with personalized greeting
st.title("📈 System Analytics")
st.write(f"Platform statistics and metrics, **{st.session_state.user_name}**")

st.divider()

# -----------------------------------------
# Platform Overview Section
# -----------------------------------------
st.subheader("🌐 Platform Overview")

# Display key metrics in columns
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Users",
        value="1,234",
        delta="+56 this week",
        help="Total registered users on the platform"
    )

with col2:
    st.metric(
        label="Assessments Today",
        value="89",
        delta="+12 from yesterday",
        help="Symptom assessments completed today"
    )

with col3:
    st.metric(
        label="Active Sessions",
        value="42",
        delta="Real-time",
        help="Users currently active on the platform"
    )

with col4:
    st.metric(
        label="System Uptime",
        value="99.9%",
        delta="Healthy",
        help="Platform availability over the last 30 days"
    )

st.divider()

# -----------------------------------------
# Usage Trends Section
# -----------------------------------------
st.subheader("📊 Usage Trends")

# Create sample data for charts
import pandas as pd

# Sample daily usage data
days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
assessments = [45, 52, 48, 61, 55, 38, 42]
users = [120, 135, 128, 145, 140, 98, 105]

# Create DataFrame
usage_df = pd.DataFrame({
    "Day": days,
    "Assessments": assessments,
    "Active Users": users
})

# Display chart
st.bar_chart(usage_df.set_index("Day"))

st.caption("Weekly usage statistics (sample data)")

st.divider()

# -----------------------------------------
# Health Regions Section
# -----------------------------------------
st.subheader("🗺️ Usage by Health Region")

# Create two columns
region_col1, region_col2 = st.columns(2)

with region_col1:
    st.markdown("**Users by Health Authority**")

    # Sample regional data
    region_data = pd.DataFrame({
        "Health Authority": [
            "Fraser Health",
            "Vancouver Coastal Health",
            "Interior Health",
            "Island Health",
            "Northern Health"
        ],
        "Users": [450, 380, 195, 145, 64]
    })

    st.dataframe(region_data, use_container_width=True, hide_index=True)

with region_col2:
    st.markdown("**Top Symptoms Reported**")

    # Sample symptom data
    symptom_data = pd.DataFrame({
        "Symptom": [
            "Headache",
            "Fatigue",
            "Sore Throat",
            "Cough",
            "Fever"
        ],
        "Reports": [234, 198, 156, 134, 98]
    })

    st.dataframe(symptom_data, use_container_width=True, hide_index=True)

st.divider()

# -----------------------------------------
# System Health Section
# -----------------------------------------
st.subheader("🖥️ System Health")

# Display system metrics
health_col1, health_col2, health_col3 = st.columns(3)

with health_col1:
    st.markdown("**Database Status**")
    st.success("✅ Connected")
    st.caption("Response time: 12ms")

with health_col2:
    st.markdown("**AI Service**")
    st.success("✅ Operational")
    st.caption("Average inference: 1.2s")

with health_col3:
    st.markdown("**API Status**")
    st.success("✅ All systems go")
    st.caption("Last check: Just now")

st.divider()

# -----------------------------------------
# Data Notice
# -----------------------------------------
st.info("""
📊 **Note:** The statistics shown above are sample/placeholder data for demonstration purposes.
Real analytics will be implemented in future sprints and connected to actual platform usage data.
""")


# -----------------------------------------
# Footer
# -----------------------------------------
st.divider()
st.caption("BC Health Platform - Monitoring system health and user engagement")
