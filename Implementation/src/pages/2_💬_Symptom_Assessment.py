# =============================================================================
# BC Health Platform - Symptom Assessment Chat Page
# =============================================================================
# Sprint 2D: Full chatbot integration with 3-layer assessment pipeline.
# Sprint 3E: Multi-turn chatbot UI enhancement
# =============================================================================

"""
AI-powered Symptom Assessment page — multi-turn conversational interface.

Uses the 3-layer hybrid classification system:
    Layer 1: OpenAI  — Extract structured symptoms from natural language
    Layer 2: Rules   — Catch life-threatening emergencies (CTAS safety layer)
    Layer 3: ML      — Classify non-critical symptoms with a trained model

Multi-turn flow (Sprint 3E):
    The chatbot asks up to 3 follow-up questions to gather duration, severity,
    and body location before triggering the final assessment pipeline.
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
from components.chatbot import initialize_dialog_state, process_multiturn_message
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

def _reset_conversation():
    """Clear dialog state and chat history to start a fresh assessment."""
    user_name = st.session_state.get("user_name", "there")
    st.session_state.dialog_state = initialize_dialog_state()
    st.session_state.chat_messages = [
        {
            "role": "assistant",
            "content": (
                f"Hello {user_name}! I'm here to help assess your symptoms. "
                "What symptoms are you experiencing today?"
            ),
            "result": None,
        }
    ]
    st.session_state.saved_assessments = set()


# Initialise on first load (or if dialog_state was never set)
if "dialog_state" not in st.session_state:
    _reset_conversation()

if "saved_assessments" not in st.session_state:
    st.session_state.saved_assessments = set()

# Convenience alias — mutations propagate because dicts are passed by reference
dialog_state: dict = st.session_state.dialog_state


# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.markdown("### 💬 Assessment Controls")

    if st.button("🔄 Start New Assessment", use_container_width=True):
        _reset_conversation()
        st.rerun()

    st.divider()

    # Live progress panel — shows what's been collected across turns
    turn_count = dialog_state.get("turn_count", 0)
    symptoms_so_far = dialog_state.get("symptoms", [])

    if turn_count > 0:
        st.markdown("**📋 Collected so far:**")
        if symptoms_so_far:
            st.markdown(f"- **Symptoms:** {', '.join(symptoms_so_far)}")
        if dialog_state.get("duration"):
            st.markdown(f"- **Duration:** {dialog_state['duration']}")
        if dialog_state.get("severity"):
            st.markdown(f"- **Severity:** {dialog_state['severity']}")
        if dialog_state.get("body_location"):
            st.markdown(f"- **Location:** {dialog_state['body_location']}")

        if dialog_state.get("assessment_complete"):
            st.success("✅ Assessment complete")
        else:
            max_turns = 3
            remaining = max(0, max_turns - turn_count)
            if remaining > 0:
                st.caption(
                    f"Up to {remaining} more question(s) before final assessment."
                )


# =============================================================================
# PAGE HEADER
# =============================================================================

st.title("💬 Symptom Assessment Chatbot")

st.warning(
    "**Important Disclaimer:** "
    "This tool provides general health information only. It is NOT a substitute "
    "for professional medical advice, diagnosis, or treatment. If you are "
    "experiencing a medical emergency, please call **911** or go to your "
    "nearest emergency room."
)

st.divider()


# =============================================================================
# HELPER — render a final assessment result card
# =============================================================================

def render_assessment_result(result: dict) -> str:
    """
    Render the full assessment result card inside the current st.chat_message
    context using live Streamlit widgets.

    Returns the pre-rendered markdown string to be stored in chat_messages so
    the history display loop can replay the same content on subsequent reruns.
    """
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
        st.markdown("**Extracted Symptoms:**")
        st.markdown(symptom_pills(result["extracted_symptoms"]), unsafe_allow_html=True)

        confidence_pct = f"{result['confidence']:.0%}"
        st.markdown(
            f"**Predicted Condition:** {result['predicted_disease']} "
            f"({confidence_pct} confidence)"
        )
        st.markdown(
            f"**Urgency:** {urgency_badge(result['urgency_level'])}",
            unsafe_allow_html=True,
        )
        st.markdown(f"**Recommendation:** {result['recommendation']}")

        st.divider()
        st.markdown("**📞 BC Health Resources**")
        st.markdown("- **HealthLink BC:** Call **8-1-1** (free health advice, 24/7)")
        if result["urgency_level"] in ("Emergency", "Urgent"):
            st.markdown(
                "- **Find nearest ER:** "
                "[BC Emergency Room Finder]"
                "(https://www.healthlinkbc.ca/health-services/search)"
            )
        st.markdown("- Find a walk-in clinic near you on the **Facility Finder** page")
        st.markdown(URGENCY_GUIDE_HTML, unsafe_allow_html=True)

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
        st.markdown("**Extracted Symptoms:**")
        st.markdown(symptom_pills(result["extracted_symptoms"]), unsafe_allow_html=True)

        st.info(
            "Our model couldn't make a confident prediction. "
            "Here's general guidance:"
        )
        st.markdown(result["recommendation"])
        st.markdown(
            f"**Urgency:** {urgency_badge(result['urgency_level'])}",
            unsafe_allow_html=True,
        )

        st.divider()
        st.markdown("**📞 BC Health Resources**")
        st.markdown("- **HealthLink BC:** Call **8-1-1** (free health advice, 24/7)")
        if result["urgency_level"] in ("Emergency", "Urgent"):
            st.markdown(
                "- **Find nearest ER:** "
                "[BC Emergency Room Finder]"
                "(https://www.healthlinkbc.ca/health-services/search)"
            )
        st.markdown("- Find a walk-in clinic near you on the **Facility Finder** page")
        st.markdown(URGENCY_GUIDE_HTML, unsafe_allow_html=True)

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

    return "\n\n".join(response_parts)


# =============================================================================
# DISPLAY CHAT HISTORY
# =============================================================================

for idx, msg in enumerate(st.session_state.chat_messages):
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.markdown(msg["content"])
        else:
            # Pre-rendered markdown (safe for follow-up text and full result cards)
            st.markdown(msg["content"], unsafe_allow_html=True)

            # Save button for final (non-emergency) assessments
            result = msg.get("result")
            if result and result.get("status") in ("ml_prediction", "openai_fallback"):
                if idx in st.session_state.saved_assessments:
                    st.markdown("✅ **Saved to your health history**")
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
# CHAT INPUT  (locked once assessment is complete)
# =============================================================================

if dialog_state.get("assessment_complete", False):
    st.info(
        "✅ Your assessment is complete. "
        "Use **🔄 Start New Assessment** in the sidebar to begin a new conversation."
    )
else:
    user_input = st.chat_input("Describe your symptoms...")

    if user_input:
        # Display the user message immediately
        st.session_state.chat_messages.append(
            {"role": "user", "content": user_input, "result": None}
        )
        with st.chat_message("user"):
            st.markdown(user_input)

        # Run one turn of the multi-turn pipeline
        with st.chat_message("assistant"):
            spinner_msg = (
                "Analyzing your symptoms..."
                if dialog_state.get("turn_count", 0) >= 2
                else "Thinking..."
            )
            with st.spinner(spinner_msg):
                result = process_multiturn_message(user_input, dialog_state)

            # ------------------------------------------------------------------
            # FOLLOW-UP — chatbot needs more information before final assessment
            # ------------------------------------------------------------------
            if result["status"] == "follow_up":
                # If no symptoms collected yet, decide based on which turn we're on.
                if not result.get("collected_symptoms"):
                    if result.get("turn_count", 1) <= 1:
                        # Turn 1: input may be vague but health-related — ask for detail
                        gentle_text = (
                            "I want to make sure I help you correctly. Could you describe "
                            "your symptoms in a bit more detail? For example, where does it "
                            "hurt, or what feels wrong?"
                        )
                        st.markdown(gentle_text)
                        st.session_state.chat_messages.append(
                            {"role": "assistant", "content": gentle_text, "result": None}
                        )
                    else:
                        # Turn 2+: still nothing extracted — show non-medical redirect
                        end_text = (
                            "I'm only able to help with health symptom assessments. "
                            "Please use **🔄 Start New Assessment** in the sidebar "
                            "whenever you're ready to describe your symptoms. Take care! 💙"
                        )
                        st.markdown(end_text)
                        dialog_state["assessment_complete"] = True
                        st.session_state.chat_messages.append(
                            {"role": "assistant", "content": end_text, "result": None}
                        )
                else:
                    follow_up_text = result["response"]
                    st.markdown(follow_up_text)
                    st.session_state.chat_messages.append(
                        {"role": "assistant", "content": follow_up_text, "result": None}
                    )

            # ------------------------------------------------------------------
            # FINAL ASSESSMENT — emergency, ML prediction, or OpenAI fallback
            # ------------------------------------------------------------------
            elif result["status"] in ("emergency", "ml_prediction", "openai_fallback"):
                rendered_content = render_assessment_result(result)
                st.session_state.chat_messages.append(
                    {
                        "role": "assistant",
                        "content": rendered_content,
                        "result": result,
                    }
                )

                # Auto-save emergencies immediately
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

            # ------------------------------------------------------------------
            # ERROR
            # ------------------------------------------------------------------
            elif result["status"] == "error":
                end_text = (
                    "I'm only able to help with health symptom assessments. "
                    "Please use **🔄 Start New Assessment** in the sidebar "
                    "whenever you're ready to describe your symptoms. Take care! 💙"
                )
                st.markdown(end_text)
                dialog_state["assessment_complete"] = True
                st.session_state.chat_messages.append(
                    {"role": "assistant", "content": end_text, "result": None}
                )

        st.rerun()


# =============================================================================
# FOOTER
# =============================================================================

st.divider()
st.caption("BC Health Platform — AI-powered health guidance for British Columbians")
