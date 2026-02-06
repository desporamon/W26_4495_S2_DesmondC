"""
BC Health Platform - Health Library Page
Sprint 1D.7: Page Protection Implementation

This page provides health information and educational resources
for users to learn about various health topics.
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
    page_title="Health Library - BC Health Platform",
    page_icon="📚",
    layout="wide"
)


# =============================================================================
# PAGE CONTENT (Only visible to authenticated users)
# =============================================================================

# Page header with personalized greeting
st.title("📚 Health Library")
st.write(f"Explore health topics and resources, **{st.session_state.user_name}**")

st.divider()

# -----------------------------------------
# Search Section
# -----------------------------------------
st.subheader("🔍 Search Health Topics")

search_query = st.text_input(
    "Search",
    placeholder="Search for health topics, conditions, or treatments...",
    label_visibility="collapsed"
)

st.divider()

# -----------------------------------------
# Featured Topics Section
# -----------------------------------------
st.subheader("⭐ Featured Topics")

# Create topic cards in columns
topic_col1, topic_col2, topic_col3 = st.columns(3)

with topic_col1:
    with st.container(border=True):
        st.markdown("### ❤️ Heart Health")
        st.write("Learn about cardiovascular health, prevention, and lifestyle tips.")
        if st.button("Read More", key="heart", use_container_width=True):
            st.info("Detailed article coming soon!")

with topic_col2:
    with st.container(border=True):
        st.markdown("### 🧠 Mental Wellness")
        st.write("Resources for stress management, anxiety, and mental health support.")
        if st.button("Read More", key="mental", use_container_width=True):
            st.info("Detailed article coming soon!")

with topic_col3:
    with st.container(border=True):
        st.markdown("### 🍎 Nutrition")
        st.write("Healthy eating guides, dietary tips, and nutrition information.")
        if st.button("Read More", key="nutrition", use_container_width=True):
            st.info("Detailed article coming soon!")

st.divider()

# -----------------------------------------
# Health Categories Section
# -----------------------------------------
st.subheader("📂 Browse by Category")

# Expandable sections for different categories
with st.expander("🩺 Common Conditions"):
    st.markdown("""
    - **Diabetes** - Understanding and managing blood sugar
    - **Hypertension** - High blood pressure basics
    - **Asthma** - Respiratory health and triggers
    - **Arthritis** - Joint health and pain management
    - **Allergies** - Common allergens and treatments
    """)
    st.caption("Click on any topic above to learn more (coming soon)")

with st.expander("💊 Medications & Treatments"):
    st.markdown("""
    - **Over-the-Counter Medications** - Safe use guidelines
    - **Prescription Medications** - What you need to know
    - **Natural Remedies** - Evidence-based alternatives
    - **Vaccinations** - Immunization schedules and info
    """)
    st.caption("Click on any topic above to learn more (coming soon)")

with st.expander("🏃 Lifestyle & Prevention"):
    st.markdown("""
    - **Exercise Guidelines** - Recommended physical activity
    - **Sleep Health** - Importance of quality rest
    - **Stress Management** - Coping strategies
    - **Preventive Screenings** - When and what to screen
    """)
    st.caption("Click on any topic above to learn more (coming soon)")

with st.expander("👶 Life Stages"):
    st.markdown("""
    - **Prenatal Care** - Pregnancy health guidelines
    - **Children's Health** - Pediatric information
    - **Senior Health** - Aging well resources
    - **Women's Health** - Gender-specific topics
    - **Men's Health** - Gender-specific topics
    """)
    st.caption("Click on any topic above to learn more (coming soon)")

st.divider()

# -----------------------------------------
# BC Health Resources Section
# -----------------------------------------
st.subheader("🏛️ BC Health Resources")

st.info("""
**Official BC Health Resources:**

- **HealthLink BC** - Call 8-1-1 for free health advice 24/7
- **BC Centre for Disease Control** - Latest public health information
- **BC Mental Health Support** - Crisis line: 1-800-784-2433
- **Poison Control Centre** - Call 1-800-567-8911

These services are available to all BC residents.
""")


# -----------------------------------------
# Footer
# -----------------------------------------
st.divider()
st.caption("BC Health Platform - Empowering you with health knowledge")
