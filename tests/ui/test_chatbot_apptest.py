# =============================================================================
# BC Health Platform — Chatbot Page Headless UI Tests (Streamlit AppTest)
# =============================================================================
# Tests the Symptom Assessment Chatbot page using Streamlit's AppTest
# framework.  All external calls (OpenAI, ML, database) are mocked so
# tests are free, deterministic, and offline.
# =============================================================================

import sys
import os
from unittest.mock import patch, MagicMock

import pytest

# ---------------------------------------------------------------------------
# Path setup — allow imports from Implementation/src/
# ---------------------------------------------------------------------------
SRC_DIR = str(
    __import__("pathlib").Path(__file__).resolve().parents[2]
    / "Implementation"
    / "src"
)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from streamlit.testing.v1 import AppTest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PAGE_PATH = os.path.join(SRC_DIR, "pages", "2_💬_Symptom_Assessment.py")

# Patch targets — patch at the SOURCE module so that `from X import Y`
# in the page script picks up the mock during at.run().
PATCH_AUTH = "components.auth.require_authentication"
PATCH_HEADER = "components.header.render_header"
PATCH_INIT_DIALOG = "components.chatbot.initialize_dialog_state"
PATCH_PROCESS_MSG = "components.chatbot.process_multiturn_message"
PATCH_SAVE = "components.database.save_assessment"

# ---------------------------------------------------------------------------
# Mock data — realistic return dicts matching the real function signatures
# ---------------------------------------------------------------------------

MOCK_DIALOG_STATE = {
    "symptoms": [],
    "duration": None,
    "severity": None,
    "body_location": None,
    "additional_info": None,
    "turn_count": 0,
    "conversation_history": [],
    "assessment_complete": False,
}

MOCK_ML_RESULT = {
    "status": "ml_prediction",
    "user_input": "I have a headache and runny nose",
    "extracted_symptoms": ["headache", "runny nose"],
    "duration": "2 days",
    "severity": "mild",
    "predicted_disease": "Common Cold",
    "confidence": 0.85,
    "urgency_level": "Self-Care",
    "recommendation": "Rest, stay hydrated, and use over-the-counter remedies.",
}

MOCK_EMERGENCY_RESULT = {
    "status": "emergency",
    "user_input": "I have chest pain and can't breathe",
    "extracted_symptoms": ["chest pain", "shortness of breath"],
    "duration": "1 hour",
    "severity": "severe",
    "rule_name": "Cardiac Arrest / Heart Attack",
    "ctas_level": 1,
    "action": "CALL 911 IMMEDIATELY",
    "description": (
        "Chest pain combined with shortness of breath may indicate a "
        "heart attack or cardiac event requiring immediate emergency care."
    ),
    "matched_symptoms": ["chest pain", "shortness of breath"],
}


# ---------------------------------------------------------------------------
# Helper — build and run the AppTest with standard mocks + session state
# ---------------------------------------------------------------------------

def _run_chatbot(authenticated=True, user_id=1, user_name="Test User",
                 process_return=None):
    """Create an AppTest for the chatbot page, set session state,
    patch external dependencies, and run it.

    Temporarily changes CWD to Implementation/src/ so that relative
    asset paths resolve correctly.

    Args:
        authenticated: Whether the user is logged in.
        user_id: The user id to set in session state.
        user_name: The user name for the welcome message.
        process_return: Return value for process_multiturn_message mock.
                        If None, process_multiturn_message is still mocked
                        but won't be called on initial load.

    Returns the AppTest instance after run() completes.
    """
    original_cwd = os.getcwd()
    try:
        os.chdir(SRC_DIR)
        with (
            patch(PATCH_AUTH),
            patch(PATCH_HEADER),
            patch(PATCH_INIT_DIALOG, return_value=dict(MOCK_DIALOG_STATE)),
            patch(PATCH_PROCESS_MSG, return_value=process_return or {}),
            patch(PATCH_SAVE, return_value=1),
        ):
            at = AppTest.from_file(PAGE_PATH)
            at.session_state["authenticated"] = authenticated
            if authenticated:
                at.session_state["user_id"] = user_id
                at.session_state["user_name"] = user_name
            at.run()
    finally:
        os.chdir(original_cwd)
    return at


def _submit_chat(at, message, process_return):
    """Submit a chat message and rerun the page with the given
    process_multiturn_message return value.

    Returns the AppTest instance after the rerun.
    """
    original_cwd = os.getcwd()
    try:
        os.chdir(SRC_DIR)
        with (
            patch(PATCH_AUTH),
            patch(PATCH_HEADER),
            patch(PATCH_INIT_DIALOG, return_value=dict(MOCK_DIALOG_STATE)),
            patch(PATCH_PROCESS_MSG, return_value=process_return),
            patch(PATCH_SAVE, return_value=1),
        ):
            at.chat_input[0].set_value(message).run()
    finally:
        os.chdir(original_cwd)
    return at


# =====================================================================
# Chatbot Page Headless UI Tests
# =====================================================================


class TestChatbotAppTest:
    """Headless UI tests for the Symptom Assessment Chatbot page.

    Every test mocks process_multiturn_message(), save_assessment(),
    require_authentication(), and render_header() so no real API calls,
    database writes, or auth checks occur.
    """

    # -----------------------------------------------------------------
    # Part 1 — Initial page load
    # -----------------------------------------------------------------

    def test_tc_ui_chat_01_page_loads_without_exception(self):
        """TC-UI-CHAT-01: The chatbot page loads without raising any
        exceptions when the user is authenticated with valid session
        state."""
        at = _run_chatbot()

        assert not at.exception, (
            f"Page raised an exception during rendering: "
            f"{[str(e) for e in at.exception]}"
        )

    def test_tc_ui_chat_02_emergency_warning_banner(self):
        """TC-UI-CHAT-02: The medical disclaimer warning banner is
        visible on initial page load (rendered via st.warning)."""
        at = _run_chatbot()

        assert not at.exception, (
            f"Page raised an exception: {[str(e) for e in at.exception]}"
        )
        assert len(at.warning) > 0, (
            "Expected at least one st.warning banner (medical disclaimer) "
            "on the chatbot page but none were found"
        )

        # Verify the warning contains key disclaimer text
        warning_text = at.warning[0].value
        assert "medical emergency" in warning_text.lower() or \
               "911" in warning_text, (
            f"Warning banner should mention medical emergency or 911, "
            f"got: {warning_text[:100]!r}"
        )

    def test_tc_ui_chat_03_welcome_message_shown(self):
        """TC-UI-CHAT-03: On initial load, a welcome message is shown
        inside a chat_message component, personalised with the user's
        name."""
        at = _run_chatbot(user_name="Alice")

        assert not at.exception, (
            f"Page raised an exception: {[str(e) for e in at.exception]}"
        )

        # The welcome message is rendered inside st.chat_message("assistant")
        assert len(at.chat_message) > 0, (
            "Expected at least one chat_message on initial load "
            "(the welcome message) but none were found"
        )

        # Check that the welcome message contains the user name
        all_chat_markdown = " ".join(
            md.value
            for cm in at.chat_message
            for md in cm.markdown
        )
        assert "Alice" in all_chat_markdown, (
            f"Welcome message should contain user name 'Alice', "
            f"got: {all_chat_markdown[:200]!r}"
        )

    # -----------------------------------------------------------------
    # Part 2 — Chat interaction
    # -----------------------------------------------------------------

    def test_tc_ui_chat_04_submit_chat_no_crash(self):
        """TC-UI-CHAT-04: User can submit a message via st.chat_input
        and the page reruns without crashing.  process_multiturn_message
        is mocked to return a follow-up response."""
        at = _run_chatbot()
        assert not at.exception, (
            f"Initial load failed: {[str(e) for e in at.exception]}"
        )

        follow_up_result = {
            "status": "follow_up",
            "user_input": "I have a headache",
            "response": "How long have you been experiencing this headache?",
            "collected_symptoms": ["headache"],
            "turn_count": 1,
        }

        at = _submit_chat(at, "I have a headache", follow_up_result)

        assert not at.exception, (
            f"Page crashed after chat submission: "
            f"{[str(e) for e in at.exception]}"
        )

    def test_tc_ui_chat_05_ml_prediction_response(self):
        """TC-UI-CHAT-05: After submitting a message, when
        process_multiturn_message returns an ml_prediction result,
        the chatbot response appears in the chat with the predicted
        condition and recommendation."""
        at = _run_chatbot()
        assert not at.exception, (
            f"Initial load failed: {[str(e) for e in at.exception]}"
        )

        at = _submit_chat(
            at, "I have a headache and runny nose", MOCK_ML_RESULT
        )

        assert not at.exception, (
            f"Page crashed after ML prediction: "
            f"{[str(e) for e in at.exception]}"
        )

        # The response should now be in chat_messages session state
        assert "chat_messages" in at.session_state, (
            "chat_messages should exist in session_state after submission"
        )
        chat_msgs = at.session_state["chat_messages"]
        assert len(chat_msgs) >= 2, (
            f"Expected at least 2 chat messages (welcome + user + response), "
            f"got {len(chat_msgs)}"
        )

        # Check that the ML prediction content appears in the page
        all_markdown = " ".join(md.value for md in at.markdown)
        assert "Common Cold" in all_markdown or \
               "Predicted Condition" in all_markdown or \
               "Rest" in all_markdown, (
            "ML prediction response should contain the predicted disease "
            "or recommendation text in the rendered output"
        )

    def test_tc_ui_chat_06_emergency_response(self):
        """TC-UI-CHAT-06: When process_multiturn_message returns an
        emergency result, the page displays emergency-level content
        including the rule name and CALL 911 action."""
        at = _run_chatbot()
        assert not at.exception, (
            f"Initial load failed: {[str(e) for e in at.exception]}"
        )

        at = _submit_chat(
            at, "I have chest pain and can't breathe",
            MOCK_EMERGENCY_RESULT,
        )

        assert not at.exception, (
            f"Page crashed after emergency response: "
            f"{[str(e) for e in at.exception]}"
        )

        # Emergency should produce an st.error element
        all_error_text = " ".join(e.value for e in at.error)
        all_markdown = " ".join(md.value for md in at.markdown)
        combined = all_error_text + " " + all_markdown

        assert "EMERGENCY" in combined or "911" in combined or \
               "Cardiac" in combined, (
            "Emergency response should contain 'EMERGENCY', '911', or "
            f"'Cardiac' in the rendered output. Errors: {all_error_text[:200]!r}, "
            f"Markdown: {all_markdown[:200]!r}"
        )

    # -----------------------------------------------------------------
    # Part 3 — Authentication guard
    # -----------------------------------------------------------------

    def test_tc_ui_chat_07_unauthenticated_blocked(self):
        """TC-UI-CHAT-07: When the user is not authenticated,
        require_authentication() blocks the page.  We let the real
        auth function run (unpatched) and verify the chatbot content
        does not render."""
        original_cwd = os.getcwd()
        try:
            os.chdir(SRC_DIR)
            with (
                patch(PATCH_HEADER),
                patch(PATCH_INIT_DIALOG,
                      return_value=dict(MOCK_DIALOG_STATE)),
                patch(PATCH_PROCESS_MSG, return_value={}),
                patch(PATCH_SAVE, return_value=1),
            ):
                at = AppTest.from_file(PAGE_PATH)
                at.session_state["authenticated"] = False
                at.run()
        finally:
            os.chdir(original_cwd)

        # When not authenticated, require_authentication calls
        # st.switch_page("app.py").  In AppTest this results in either:
        # - an exception, or
        # - the page content not rendering (no chat_input, no title)
        has_chat_input = len(at.chat_input) > 0

        if at.exception:
            # switch_page raised — auth guard fired correctly
            pass
        else:
            assert not has_chat_input, (
                "Chatbot page should NOT render chat input for "
                "unauthenticated users — auth guard did not fire"
            )

    def test_tc_ui_chat_08_chat_history_persists(self):
        """TC-UI-CHAT-08: After submitting a chat message, the chat
        history in session_state.chat_messages contains at least the
        welcome message, the user's message, and the assistant's
        response."""
        at = _run_chatbot()
        assert not at.exception, (
            f"Initial load failed: {[str(e) for e in at.exception]}"
        )

        # Initial state: welcome message only
        assert "chat_messages" in at.session_state, (
            "chat_messages should exist in session_state on initial load"
        )
        initial_count = len(at.session_state["chat_messages"])
        assert initial_count >= 1, (
            f"Expected at least 1 chat message (welcome) on initial load, "
            f"got {initial_count}"
        )

        at = _submit_chat(
            at, "I feel nauseous", MOCK_ML_RESULT
        )

        assert not at.exception, (
            f"Page crashed after submission: "
            f"{[str(e) for e in at.exception]}"
        )

        final_messages = at.session_state["chat_messages"]
        assert len(final_messages) >= 3, (
            f"After submitting a message, chat_messages should contain "
            f"at least 3 entries (welcome + user + assistant response), "
            f"got {len(final_messages)}"
        )

        # Verify the user message was stored
        user_messages = [m for m in final_messages if m["role"] == "user"]
        assert len(user_messages) >= 1, (
            "Chat history should contain at least one user message "
            "after submission"
        )
