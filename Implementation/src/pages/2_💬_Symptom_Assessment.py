# =============================================================================
# BC Health Platform - Symptom Assessment Chat Page
# =============================================================================
# Sprint 2D: Full chatbot integration with 3-layer assessment pipeline.
# =============================================================================

"""
AI-powered Symptom Assessment page with real-time chat interface.

Uses the 3-layer hybrid classification system:
    Layer 1: OpenAI  — Extract structured symptoms from natural language
    Layer 2: Rules   — Catch life-threatening emergencies (CTAS safety layer)
    Layer 3: ML      — Classify non-critical symptoms with a trained model
"""

import streamlit as st
from components.auth import require_authentication

# =============================================================================
# PAGE PROTECTION — Must be logged in to view this page
# =============================================================================
require_authentication()

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="Symptom Assessment - BC Health Platform",
    page_icon="💬",
    layout="wide",
)

# =============================================================================
# IMPORTS (after page config)
# =============================================================================

from components.header import render_header
from components.chatbot import run_assessment
from components.database import save_assessment

render_header()


# =============================================================================
# URGENCY COLOUR HELPERS
# =============================================================================

URGENCY_COLOURS = {
    "Emergency": ("🔴", "#FF4B4B"),
    "Urgent":    ("🟠", "#FFA500"),
    "Routine":   ("🟡", "#FFD700"),
    "Self-Care": ("🟢", "#00CC66"),
}


def urgency_badge(level: str) -> str:
    """Return an HTML-styled urgency badge."""
    icon, colour = URGENCY_COLOURS.get(level, ("🟡", "#FFD700"))
    return (
        f'<span style="background-color:{colour};color:#fff;padding:4px 12px;'
        f'border-radius:12px;font-weight:bold;font-size:0.9em;">'
        f'{icon} {level}</span>'
    )


def symptom_pills(symptoms: list) -> str:
    """Return extracted symptoms as styled pill tags."""
    pills = "".join(
        f'<span style="background-color:#E8F0FE;color:#1A73E8;'
        f'padding:4px 10px;border-radius:16px;margin:2px 4px;'
        f'display:inline-block;font-size:0.85em;">{s}</span>'
        for s in symptoms
    )
    return pills


URGENCY_GUIDE_HTML = (
    '<div style="background-color:#F8F9FA;border:1px solid #DEE2E6;'
    'border-radius:8px;padding:10px 14px;margin-top:8px;font-size:0.85em;">'
    '<strong>Urgency Level Guide</strong>'
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:4px 24px;margin-top:6px;">'
    '<span><span style="color:#FF4B4B;">&#x1F534;</span> <strong>Emergency</strong> (Call 911)</span>'
    '<span><span style="color:#FFA500;">&#x1F7E0;</span> <strong>Urgent</strong> (ED / Urgent Care)</span>'
    '<span><span style="color:#DAA520;">&#x1F7E1;</span> <strong>Routine</strong> (Walk-in / Doctor)</span>'
    '<span><span style="color:#00CC66;">&#x1F7E2;</span> <strong>Self-Care</strong> (Home care)</span>'
    '</div></div>'
)


# =============================================================================
# SESSION STATE INITIALISATION
# =============================================================================

if "chat_messages" not in st.session_state:
    user_name = st.session_state.get("user_name", "there")
    st.session_state.chat_messages = [
        {
            "role": "assistant",
            "content": (
                f"Hello {user_name}! I'm here to help assess your symptoms "
                "and guide you to the right care. What symptoms are you "
                "experiencing today?"
            ),
            "result": None,
        }
    ]
if "saved_assessments" not in st.session_state:
    st.session_state.saved_assessments = set()


# =============================================================================
# SIDEBAR — Clear chat button
# =============================================================================

with st.sidebar:
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.chat_messages = []
        st.rerun()


# =============================================================================
# PAGE HEADER
# =============================================================================

st.title("💬 Symptom Assessment")

st.warning(
    "**Important Disclaimer:** "
    "This tool provides general health information only. It is NOT a substitute "
    "for professional medical advice, diagnosis, or treatment. If you are "
    "experiencing a medical emergency, please call **911** or go to your "
    "nearest emergency room."
)

st.divider()


# =============================================================================
# DISPLAY CHAT HISTORY
# =============================================================================

for idx, msg in enumerate(st.session_state.chat_messages):
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.markdown(msg["content"])
        else:
            # Assistant messages store pre-rendered content and the raw result
            st.markdown(msg["content"], unsafe_allow_html=True)

            # Show Save / Saved for saveable results
            result = msg.get("result")
            if result and result.get("status") in ("ml_prediction", "openai_fallback"):
                if idx in st.session_state.saved_assessments:
                    st.markdown("✅ Saved")
                else:
                    if st.button("💾 Save Assessment", key=f"save_hist_{idx}"):
                        saved_id = save_assessment(
                            user_id=st.session_state.user_id,
                            symptoms=result["user_input"],
                            extracted_symptoms=result["extracted_symptoms"],
                            urgency_level=result["urgency_level"],
                            recommendation=result["recommendation"],
                        )
                        if saved_id:
                            st.session_state.saved_assessments.add(idx)
                            st.rerun()
                        else:
                            st.error("Failed to save assessment. Please try again.")


# =============================================================================
# CHAT INPUT
# =============================================================================

user_input = st.chat_input("Describe your symptoms...")

if user_input:
    # --- Add and display the user message ---
    st.session_state.chat_messages.append(
        {"role": "user", "content": user_input, "result": None}
    )
    with st.chat_message("user"):
        st.markdown(user_input)

    # --- Run the 3-layer assessment ---
    with st.chat_message("assistant"):
        with st.spinner("Analyzing your symptoms..."):
            result = run_assessment(user_input)

        # -----------------------------------------------------------------
        # BUILD THE ASSISTANT RESPONSE BASED ON STATUS
        # -----------------------------------------------------------------
        response_parts = []

        # ==================== EMERGENCY ====================
        if result["status"] == "emergency":
            st.error(f"🚨 **EMERGENCY DETECTED — {result['rule_name']}**")
            st.markdown(f"**⚠️ {result['action']}**")
            st.markdown(result["description"])
            st.markdown(
                f"**CTAS Level:** {result['ctas_level']} &nbsp;|&nbsp; "
                f"**Matched symptoms:** {', '.join(result['matched_symptoms'])}"
            )
            st.markdown(
                f"**Urgency:** {urgency_badge('Emergency')}",
                unsafe_allow_html=True,
            )
            st.markdown(URGENCY_GUIDE_HTML, unsafe_allow_html=True)

            response_parts.append(
                f"🚨 **EMERGENCY DETECTED — {result['rule_name']}**\n\n"
                f"**⚠️ {result['action']}**\n\n"
                f"{result['description']}\n\n"
                f"**CTAS Level:** {result['ctas_level']} &nbsp;|&nbsp; "
                f"**Matched symptoms:** {', '.join(result['matched_symptoms'])}\n\n"
                f"**Urgency:** {urgency_badge('Emergency')}\n\n"
                f"{URGENCY_GUIDE_HTML}"
            )

        # ==================== ML PREDICTION ====================
        elif result["status"] == "ml_prediction":
            # Extracted symptoms
            st.markdown("**Extracted Symptoms:**")
            st.markdown(symptom_pills(result["extracted_symptoms"]),
                        unsafe_allow_html=True)

            # Prediction
            confidence_pct = f"{result['confidence']:.0%}"
            st.markdown(
                f"**Predicted Condition:** {result['predicted_disease']} "
                f"({confidence_pct} confidence)"
            )

            # Urgency badge
            st.markdown(
                f"**Urgency:** {urgency_badge(result['urgency_level'])}",
                unsafe_allow_html=True,
            )

            # Recommendation
            st.markdown(f"**Recommendation:** {result['recommendation']}")

            # BC Health Resources
            st.divider()
            st.markdown("**📞 BC Health Resources**")
            st.markdown("- **HealthLink BC:** Call **8-1-1** (free health advice, 24/7)")
            if result["urgency_level"] in ("Emergency", "Urgent"):
                st.markdown(
                    "- **Find nearest ER:** "
                    "[BC Emergency Room Finder]"
                    "(https://www.healthlinkbc.ca/health-services/search)"
                )
            st.markdown(
                "- Find a walk-in clinic near you on the **Facility Finder** page"
            )
            st.markdown(URGENCY_GUIDE_HTML, unsafe_allow_html=True)

            # Store for history
            response_parts.append(
                f"**Extracted Symptoms:** {', '.join(result['extracted_symptoms'])}\n\n"
                f"**Predicted Condition:** {result['predicted_disease']} "
                f"({confidence_pct} confidence)\n\n"
                f"**Urgency:** {urgency_badge(result['urgency_level'])}\n\n"
                f"**Recommendation:** {result['recommendation']}\n\n---\n\n"
                f"**📞 BC Health Resources**\n"
                f"- **HealthLink BC:** Call **8-1-1** (free health advice, 24/7)\n"
                f"- Find a walk-in clinic near you on the **Facility Finder** page\n\n"
                f"{URGENCY_GUIDE_HTML}"
            )

        # ==================== OPENAI FALLBACK ====================
        elif result["status"] == "openai_fallback":
            # Extracted symptoms
            st.markdown("**Extracted Symptoms:**")
            st.markdown(symptom_pills(result["extracted_symptoms"]),
                        unsafe_allow_html=True)

            st.info(
                "Our model couldn't make a confident prediction. "
                "Here's general guidance:"
            )
            st.markdown(result["recommendation"])

            # Urgency badge
            st.markdown(
                f"**Urgency:** {urgency_badge(result['urgency_level'])}",
                unsafe_allow_html=True,
            )

            # BC Health Resources
            st.divider()
            st.markdown("**📞 BC Health Resources**")
            st.markdown("- **HealthLink BC:** Call **8-1-1** (free health advice, 24/7)")
            if result["urgency_level"] in ("Emergency", "Urgent"):
                st.markdown(
                    "- **Find nearest ER:** "
                    "[BC Emergency Room Finder]"
                    "(https://www.healthlinkbc.ca/health-services/search)"
                )
            st.markdown(
                "- Find a walk-in clinic near you on the **Facility Finder** page"
            )
            st.markdown(URGENCY_GUIDE_HTML, unsafe_allow_html=True)

            # Store for history
            response_parts.append(
                f"**Extracted Symptoms:** {', '.join(result['extracted_symptoms'])}\n\n"
                f"Our model couldn't make a confident prediction. "
                f"Here's general guidance:\n\n"
                f"{result['recommendation']}\n\n"
                f"**Urgency:** {urgency_badge(result['urgency_level'])}\n\n---\n\n"
                f"**📞 BC Health Resources**\n"
                f"- **HealthLink BC:** Call **8-1-1** (free health advice, 24/7)\n"
                f"- Find a walk-in clinic near you on the **Facility Finder** page\n\n"
                f"{URGENCY_GUIDE_HTML}"
            )

        # ==================== ERROR ====================
        elif result["status"] == "error":
            st.error(f"❌ {result['error']}")
            response_parts.append(f"❌ {result['error']}")

        # --- Save assistant message to chat history ---
        assistant_content = "\n\n".join(response_parts)
        st.session_state.chat_messages.append(
            {"role": "assistant", "content": assistant_content, "result": result}
        )

        # Auto-save emergency results to the database
        if result["status"] == "emergency":
            save_assessment(
                user_id=st.session_state.user_id,
                symptoms=result["user_input"],
                extracted_symptoms=result.get(
                    "extracted_symptoms", result.get("matched_symptoms", [])
                ),
                urgency_level="Emergency",
                recommendation=result["action"],
            )

        # Rerun so the history loop renders the new message with Save button
        st.rerun()


# =============================================================================
# FOOTER
# =============================================================================

st.divider()
st.caption("BC Health Platform — AI-powered health guidance for British Columbians")
