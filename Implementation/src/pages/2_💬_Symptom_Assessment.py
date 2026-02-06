"""
BC Health Platform - Symptom Assessment Page
Sprint 1D.7: Page Protection Implementation

This page provides AI-powered symptom assessment functionality.
Users can describe their symptoms and receive health guidance.
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
    page_title="Symptom Assessment - BC Health Platform",
    page_icon="💬",
    layout="wide"
)


# =============================================================================
# PAGE CONTENT (Only visible to authenticated users)
# =============================================================================

# Page header with personalized greeting
st.title("💬 Symptom Assessment")
st.write(f"Hello, **{st.session_state.user_name}**! Let's check your symptoms.")

st.divider()

# -----------------------------------------
# Disclaimer
# -----------------------------------------
st.warning("""
**Important Disclaimer:**
This tool provides general health information only. It is NOT a substitute
for professional medical advice, diagnosis, or treatment. If you're experiencing
a medical emergency, please call 911 or go to your nearest emergency room.
""")

st.divider()

# -----------------------------------------
# Symptom Input Section
# -----------------------------------------
st.subheader("📝 Describe Your Symptoms")

# Text area for symptom description
symptoms = st.text_area(
    "What symptoms are you experiencing?",
    placeholder="Example: I have a headache and feel tired. My throat is sore and I have a slight fever.",
    height=150,
    help="Be as specific as possible. Include when symptoms started and their severity."
)

# Duration selector
st.subheader("⏱️ How long have you had these symptoms?")
duration = st.selectbox(
    "Duration",
    options=[
        "Select duration",
        "Less than 24 hours",
        "1-3 days",
        "4-7 days",
        "1-2 weeks",
        "More than 2 weeks"
    ],
    label_visibility="collapsed"
)

# Severity slider
st.subheader("📊 How would you rate the severity?")
severity = st.slider(
    "Severity (1 = Mild, 10 = Severe)",
    min_value=1,
    max_value=10,
    value=5,
    help="1 = Barely noticeable, 10 = Worst pain/discomfort imaginable"
)

st.divider()

# -----------------------------------------
# Submit Button
# -----------------------------------------
if st.button("🔍 Analyze Symptoms", use_container_width=True, type="primary"):
    if not symptoms.strip():
        st.error("Please describe your symptoms before submitting.")
    elif duration == "Select duration":
        st.error("Please select how long you've had these symptoms.")
    else:
        # Placeholder for actual AI analysis (to be implemented in future sprint)
        with st.spinner("Analyzing your symptoms..."):
            import time
            time.sleep(2)  # Simulate processing time

        st.success("Assessment complete! Here's what we found:")

        # Placeholder results
        st.info("""
        **Preliminary Assessment:**

        Based on your symptoms, you may be experiencing a common cold or
        upper respiratory infection. However, this is just a preliminary
        assessment based on limited information.

        **Recommended Actions:**
        - Rest and stay hydrated
        - Monitor your symptoms
        - Consider over-the-counter medications for symptom relief
        - If symptoms worsen or persist beyond 7 days, consult a healthcare provider

        **When to Seek Immediate Care:**
        - Difficulty breathing
        - High fever (over 39°C/102°F)
        - Symptoms suddenly get much worse
        """)

        st.caption("Note: This assessment will be saved to your dashboard.")


# -----------------------------------------
# Footer
# -----------------------------------------
st.divider()
st.caption("BC Health Platform - AI-powered health guidance for British Columbians")
