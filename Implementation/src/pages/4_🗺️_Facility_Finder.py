"""
BC Health Platform - Facility Finder Page
Sprint 1D.7: Page Protection Implementation

This page helps users find nearby healthcare facilities
such as hospitals, clinics, and pharmacies in British Columbia.
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
    page_title="Facility Finder - BC Health Platform",
    page_icon="🗺️",
    layout="wide"
)

from components.header import render_header
render_header()


# =============================================================================
# PAGE CONTENT (Only visible to authenticated users)
# =============================================================================

# Page header with personalized greeting
st.title("🗺️ Facility Finder")
st.write(f"Find healthcare facilities near you, **{st.session_state.user_name}**")

st.divider()

# -----------------------------------------
# Search Section
# -----------------------------------------
st.subheader("🔍 Search for Healthcare Facilities")

# Create search filters in columns
filter_col1, filter_col2 = st.columns(2)

with filter_col1:
    # Location input
    location = st.text_input(
        "📍 Your Location",
        placeholder="Enter your city or postal code",
        help="Enter your city name or postal code to find nearby facilities"
    )

with filter_col2:
    # Facility type selector
    facility_type = st.selectbox(
        "🏥 Facility Type",
        options=[
            "All Facilities",
            "Hospitals",
            "Walk-in Clinics",
            "Family Doctors",
            "Pharmacies",
            "Urgent Care Centers",
            "Mental Health Services"
        ]
    )

# Additional filters
st.subheader("⚙️ Additional Filters")

filter_col3, filter_col4 = st.columns(2)

with filter_col3:
    # Distance slider
    distance = st.slider(
        "Maximum Distance (km)",
        min_value=1,
        max_value=50,
        value=10,
        help="Maximum distance from your location"
    )

with filter_col4:
    # Open now checkbox
    open_now = st.checkbox("Open Now", value=False, help="Only show facilities currently open")
    accepts_walkins = st.checkbox("Accepts Walk-ins", value=False, help="Only show facilities that accept walk-in patients")

st.divider()

# Search button
if st.button("🔍 Search Facilities", use_container_width=True, type="primary"):
    if not location.strip():
        st.error("Please enter your location to search for facilities.")
    else:
        with st.spinner("Searching for facilities..."):
            import time
            time.sleep(1.5)  # Simulate search time

        st.success(f"Found 5 {facility_type.lower()} within {distance}km of '{location}'")

        # Placeholder results
        st.divider()

        # Sample facility cards
        for i in range(3):
            with st.container():
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"### 🏥 Sample Healthcare Facility {i+1}")
                    st.write(f"📍 123 Example Street, {location}")
                    st.write("📞 (604) 555-0100")
                    st.caption("⭐ 4.5/5 • Open 8:00 AM - 8:00 PM")

                with col2:
                    st.metric("Distance", f"{(i+1) * 2.5:.1f} km")
                    st.button("📍 Directions", key=f"dir_{i}", use_container_width=True)

                st.divider()

        st.info("Note: This is placeholder data. Real facility data will be integrated in a future sprint.")

# -----------------------------------------
# BC Health Authorities Info
# -----------------------------------------
st.subheader("🏛️ BC Health Authorities")

st.markdown("""
British Columbia's healthcare is organized into five regional health authorities:

| Health Authority | Region |
|-----------------|--------|
| Fraser Health | Surrey, Burnaby, New Westminster, and Fraser Valley |
| Vancouver Coastal Health | Vancouver, Richmond, North Shore, and Sea-to-Sky |
| Interior Health | Kelowna, Kamloops, and the BC Interior |
| Island Health | Vancouver Island and surrounding islands |
| Northern Health | Prince George and Northern BC |
""")


# -----------------------------------------
# Footer
# -----------------------------------------
st.divider()
st.caption("BC Health Platform - Connecting you with healthcare across British Columbia")
