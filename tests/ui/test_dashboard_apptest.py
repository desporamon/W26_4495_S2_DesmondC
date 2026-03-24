# =============================================================================
# BC Health Platform — Dashboard Headless UI Tests (Streamlit AppTest)
# =============================================================================
# Tests the My Personal Health Dashboard page using Streamlit's AppTest
# framework.  All database calls are mocked so no real health_platform.db
# is touched and no Streamlit server is required.
# =============================================================================

import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime

import pytest

# ---------------------------------------------------------------------------
# Path setup — allow imports from Implementation/src/ so that the page
# file's `from components.* import ...` statements resolve correctly.
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
PAGE_PATH = os.path.join(SRC_DIR, "pages", "3_📊_My_Dashboard.py")

# Patch targets — patch at the SOURCE module so that `from X import Y`
# in the page script picks up the mock during at.run().
PATCH_AUTH = "components.auth.require_authentication"
PATCH_HEADER = "components.header.render_header"
PATCH_GET_ASSESSMENTS = "components.database.get_user_assessments"

# ---------------------------------------------------------------------------
# Mock data — 3 realistic assessment dicts
# ---------------------------------------------------------------------------
MOCK_ASSESSMENTS = [
    {
        "id": 1,
        "user_id": 1,
        "symptoms": "chest pain",
        "urgency_level": "Emergency",
        "recommendation": "Call 911",
        "created_at": "2026-03-15 10:00:00",
        "extracted_symptoms": ["chest pain"],
    },
    {
        "id": 2,
        "user_id": 1,
        "symptoms": "headache",
        "urgency_level": "Routine",
        "recommendation": "Rest at home",
        "created_at": "2026-03-16 14:00:00",
        "extracted_symptoms": ["headache"],
    },
    {
        "id": 3,
        "user_id": 1,
        "symptoms": "fever cough",
        "urgency_level": "Urgent",
        "recommendation": "See a doctor today",
        "created_at": "2026-03-17 09:00:00",
        "extracted_symptoms": ["fever", "cough"],
    },
]


# ---------------------------------------------------------------------------
# Helper — build and run the AppTest with standard mocks + session state
# ---------------------------------------------------------------------------

def _run_dashboard(assessments=None, authenticated=True, user_id=1,
                   user_name="Test User"):
    """Create an AppTest for the dashboard page, set session state,
    patch external dependencies, and run it.

    Temporarily changes the working directory to Implementation/src/
    so that relative asset paths (e.g. 'assets/logo.png') resolve
    correctly, then restores the original CWD afterwards.

    Returns the AppTest instance after run() completes.
    """
    if assessments is None:
        assessments = MOCK_ASSESSMENTS

    original_cwd = os.getcwd()
    try:
        os.chdir(SRC_DIR)
        with (
            patch(PATCH_AUTH),
            patch(PATCH_HEADER),
            patch(PATCH_GET_ASSESSMENTS, return_value=assessments),
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


# =====================================================================
# Dashboard Headless UI Tests
# =====================================================================


class TestDashboardAppTest:
    """Headless UI tests for the My Personal Health Dashboard page.

    Every test mocks get_user_assessments(), require_authentication(),
    and render_header() so no real database or auth layer is needed.
    """

    # -----------------------------------------------------------------
    # Part 1 — Page loads correctly
    # -----------------------------------------------------------------

    def test_tc_ui_dash_01_page_loads_without_exception(self):
        """TC-UI-DASH-01: The dashboard page loads without raising any
        exceptions when the user is authenticated with valid session
        state and mock assessment data."""
        at = _run_dashboard()

        assert not at.exception, (
            f"Page raised an exception during rendering: "
            f"{[str(e) for e in at.exception]}"
        )

    def test_tc_ui_dash_02_page_renders_title(self):
        """TC-UI-DASH-02: The page renders the dashboard title or header
        text 'My Personal Health Dashboard' somewhere in the page
        output (rendered as HTML inside st.markdown)."""
        at = _run_dashboard()

        assert not at.exception, (
            f"Page raised an exception: {[str(e) for e in at.exception]}"
        )

        # The title is rendered via st.markdown with HTML containing
        # "My Personal Health Dashboard"
        found_title = False
        for md in at.markdown:
            if "My Personal Health Dashboard" in md.value:
                found_title = True
                break

        assert found_title, (
            "Expected 'My Personal Health Dashboard' in page markdown "
            "output but it was not found"
        )

    def test_tc_ui_dash_03_stat_cards_present(self):
        """TC-UI-DASH-03: The 4 summary stat cards are rendered.  Since
        they use custom HTML via st.markdown (not st.metric), we verify
        that all 4 stat card header texts appear in the rendered markdown
        and that the 2 selectbox filters are present as a proxy for
        successful full-page rendering."""
        at = _run_dashboard()

        assert not at.exception, (
            f"Page raised an exception: {[str(e) for e in at.exception]}"
        )

        # Check all 4 stat card headers appear in the page markdown
        stat_headers = [
            "Total Checks",
            "This Month",
            "Most Common",
            "Avg Urgency",
        ]
        all_markdown = " ".join(md.value for md in at.markdown)

        for header in stat_headers:
            assert header in all_markdown, (
                f"Stat card '{header}' not found in rendered markdown"
            )

        # Selectboxes present confirms the page rendered past the stat
        # cards and into the filter section
        assert len(at.selectbox) >= 2, (
            f"Expected at least 2 selectboxes (date range + urgency), "
            f"got {len(at.selectbox)}"
        )

    # -----------------------------------------------------------------
    # Part 2 — Data display
    # -----------------------------------------------------------------

    def test_tc_ui_dash_04_date_range_filter_present(self):
        """TC-UI-DASH-04: The date range selectbox and urgency filter
        selectbox are both present on the page."""
        at = _run_dashboard()

        assert not at.exception, (
            f"Page raised an exception: {[str(e) for e in at.exception]}"
        )

        assert len(at.selectbox) == 2, (
            f"Expected exactly 2 selectboxes, got {len(at.selectbox)}"
        )

        # Verify the selectbox options contain the expected filter values
        selectbox_options = [sb.options for sb in at.selectbox]
        all_options_flat = [
            opt for opts in selectbox_options for opt in opts
        ]

        assert "All Time" in all_options_flat, (
            "Date range filter should contain 'All Time' option"
        )
        assert "Last 3 Months" in all_options_flat, (
            "Date range filter should contain 'Last 3 Months' option"
        )
        assert "All Urgency Levels" in all_options_flat, (
            "Urgency filter should contain 'All Urgency Levels' option"
        )

    def test_tc_ui_dash_05_charts_render(self):
        """TC-UI-DASH-05: Plotly charts render without exceptions.
        AppTest does not render charts visually, so we verify that
        the page completed rendering without errors — which proves
        the chart construction logic (go.Figure, go.Scatter, go.Pie)
        executed successfully."""
        at = _run_dashboard()

        assert not at.exception, (
            f"Page raised an exception during chart rendering: "
            f"{[str(e) for e in at.exception]}"
        )

        # The page rendered fully — selectboxes after the chart section
        # confirm we got past the Plotly chart construction
        assert len(at.selectbox) >= 2, (
            "Selectboxes should be present, confirming the page rendered "
            "past the chart section without errors"
        )

    def test_tc_ui_dash_06_empty_state_no_crash(self):
        """TC-UI-DASH-06: When the user has no assessments, the page
        loads without crashing and shows an appropriate empty-state
        message instead of charts."""
        at = _run_dashboard(assessments=[])

        assert not at.exception, (
            f"Page crashed with no assessments: "
            f"{[str(e) for e in at.exception]}"
        )

        # Check for empty-state messages in the rendered markdown
        all_markdown = " ".join(md.value for md in at.markdown)
        has_empty_msg = (
            "No assessment" in all_markdown
            or "No symptom data" in all_markdown
            or "empty-msg" in all_markdown
        )
        assert has_empty_msg, (
            "Expected an empty-state message when user has no assessments"
        )

    # -----------------------------------------------------------------
    # Part 3 — Authentication guard
    # -----------------------------------------------------------------

    def test_tc_ui_dash_07_unauthenticated_redirect(self):
        """TC-UI-DASH-07: When the user is not authenticated,
        require_authentication() calls st.switch_page which prevents
        the dashboard content from rendering.  We let the real auth
        function run (unpatched) and verify the page either raises
        an exception or does not render the dashboard content."""
        original_cwd = os.getcwd()
        try:
            os.chdir(SRC_DIR)
            with (
                patch(PATCH_HEADER),
                patch(PATCH_GET_ASSESSMENTS, return_value=[]),
            ):
                at = AppTest.from_file(PAGE_PATH)
                at.session_state["authenticated"] = False
                at.run()
        finally:
            os.chdir(original_cwd)

        # When not authenticated, require_authentication calls
        # st.switch_page("app.py").  In AppTest this results in either:
        # - an exception (StreamlitAPIException), or
        # - the page content not rendering (no selectboxes, no stat cards)
        dashboard_rendered = len(at.selectbox) >= 2

        if at.exception:
            # switch_page raised — auth guard fired correctly
            pass
        else:
            assert not dashboard_rendered, (
                "Dashboard content should NOT render for unauthenticated "
                "users — selectboxes are present, meaning the auth "
                "guard did not fire"
            )

    def test_tc_ui_dash_08_user_data_isolation(self):
        """TC-UI-DASH-08: The page only loads assessments for the
        current session user_id.  We verify that get_user_assessments
        is called with the correct user_id from session_state, not a
        hardcoded value or another user's id."""
        target_user_id = 42

        original_cwd = os.getcwd()
        try:
            os.chdir(SRC_DIR)
            with (
                patch(PATCH_AUTH),
                patch(PATCH_HEADER),
                patch(PATCH_GET_ASSESSMENTS, return_value=[])
                    as mock_get,
            ):
                at = AppTest.from_file(PAGE_PATH)
                at.session_state["authenticated"] = True
                at.session_state["user_id"] = target_user_id
                at.session_state["user_name"] = "Isolated User"
                at.run()
        finally:
            os.chdir(original_cwd)

        assert not at.exception, (
            f"Page raised an exception: {[str(e) for e in at.exception]}"
        )

        # Verify get_user_assessments was called with the correct user_id
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        actual_user_id = call_args[0][0]  # first positional arg

        assert actual_user_id == target_user_id, (
            f"get_user_assessments was called with user_id={actual_user_id}, "
            f"expected {target_user_id} — page may be using a hardcoded id "
            f"instead of session_state.user_id"
        )
