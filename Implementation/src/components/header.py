# =============================================================================
# BC Health Platform - Shared Header Banner
# =============================================================================

"""
Shared header component rendered at the top of every page.

Displays a fixed full-width teal banner with the app logo, title, username,
and logout link. Call render_header() on each page after
require_authentication() and st.set_page_config().

The sidebar CSS is injected BEFORE any auth check so that the styled sidebar
appears instantly on every page load, eliminating the flash of unstyled content.
"""

import base64
import os

import streamlit as st


# =============================================================================
# LOGO LOADING
# =============================================================================

_LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png")


@st.cache_data
def get_logo_base64() -> str:
    """Load logo.png and return as a base64 string for HTML embedding."""
    with open(_LOGO_PATH, "rb") as f:
        return base64.b64encode(f.read()).decode()


# =============================================================================
# GLOBAL CSS (always injected, regardless of auth state)
# =============================================================================

_GLOBAL_CSS = """
<style>
/* ---- Hide the default Streamlit header ---- */
header[data-testid="stHeader"] {
    display: none !important;
}

/* ---- Sidebar styling ---- */
/* Light cyan sidebar background */
section[data-testid="stSidebar"] {
    background-color: #D4EFFC !important;
}
section[data-testid="stSidebar"] > div {
    background-color: #D4EFFC !important;
}

/* Hide the "app" label at the top of sidebar nav */
[data-testid="stSidebarNav"] li:first-child {
    display: none !important;
}

/* Sidebar nav links - darker, bolder text */
[data-testid="stSidebarNav"] a {
    color: #1a1a1a !important;
    font-weight: 600 !important;
    font-size: 0.95em !important;
    padding: 0.5rem 1rem !important;
    border-radius: 8px !important;
    margin: 2px 8px !important;
    transition: background 0.2s, color 0.2s !important;
}

/* Monochrome (grayscale) icons for inactive tabs */
[data-testid="stSidebarNav"] a span {
    filter: grayscale(100%) !important;
}

/* Inactive tab hover */
[data-testid="stSidebarNav"] a:hover {
    background-color: rgba(0, 98, 113, 0.1) !important;
    color: #006271 !important;
}

/* Active tab - teal background with white text */
[data-testid="stSidebarNav"] a[aria-current="page"] {
    background-color: #006271 !important;
    color: #ffffff !important;
    font-weight: 700 !important;
}

/* Active tab icons - white */
[data-testid="stSidebarNav"] a[aria-current="page"] span {
    filter: grayscale(100%) brightness(10) !important;
}
</style>
"""

# CSS added ONLY when the user is authenticated (banner + sidebar offset)
_BANNER_CSS = """
<style>
/* ---- Fixed full-width banner ---- */
.bc-header {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 60px;
    background-color: #006271;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 24px;
    box-sizing: border-box;
    z-index: 999;
    box-shadow: 0 2px 4px rgba(0,0,0,0.15);
}

/* ---- Push main content below the banner ---- */
.main .block-container {
    padding-top: 80px !important;
}

/* ---- Force sidebar visible and push below the banner ---- */
section[data-testid="stSidebar"] {
    display: block !important;
    visibility: visible !important;
    width: 245px !important;
    min-width: 245px !important;
    transform: none !important;
    opacity: 1 !important;
    top: 60px !important;
    height: calc(100vh - 60px) !important;
}
section[data-testid="stSidebar"] > div {
    padding-top: 1rem;
}

/* ---- Ensure sidebar toggle is visible ---- */
[data-testid="stSidebarCollapsedControl"] {
    display: block !important;
    visibility: visible !important;
}

/* ---- Logout link styled as button ---- */
.bc-header .logout-link {
    color: #fff;
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.4);
    padding: 5px 16px;
    border-radius: 6px;
    text-decoration: none;
    font-size: 0.85em;
    font-weight: 500;
    margin-left: 16px;
    transition: background 0.2s;
}
.bc-header .logout-link:hover {
    background: rgba(255,255,255,0.3);
    color: #fff;
}
</style>
"""

# CSS to completely hide sidebar (used on login page)
_HIDE_SIDEBAR_CSS = """
<style>
section[data-testid="stSidebar"] {
    display: none !important;
}
button[data-testid="stSidebarCollapsedControl"] {
    display: none !important;
}
</style>
"""


# =============================================================================
# LOGOUT HELPER
# =============================================================================

def _logout():
    """Clear all session state and query params, then redirect to login."""
    st.query_params.clear()
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.switch_page("app.py")


# =============================================================================
# PUBLIC API
# =============================================================================

def inject_global_css():
    """Inject sidebar and global CSS immediately, before any content renders.

    Call this as the very first thing after st.set_page_config() on pages
    where render_header() is NOT used (e.g. app.py login view).
    """
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)


def hide_sidebar():
    """Completely hide the sidebar and its toggle button.

    Use on pages where navigation should not be visible (e.g. login page).
    """
    st.markdown(_HIDE_SIDEBAR_CSS, unsafe_allow_html=True)


def render_header():
    """
    Render global CSS + fixed full-width banner above all page content.

    1. Injects sidebar / global CSS immediately (no auth check).
    2. Handles pending logout via ``?logout=1`` query param.
    3. If authenticated, renders the teal banner with logo, title,
       username, and logout link.

    Call this on every page right after st.set_page_config().
    """
    # ---- Step 1: Always inject global CSS first (eliminates FOUC) ----
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)

    # ---- Step 2: Handle pending logout triggered by the banner link ----
    if st.query_params.get("logout") == "1":
        _logout()
        return

    # ---- Step 3: Only show banner when authenticated ----
    if not st.session_state.get("authenticated", False):
        return

    user_name = st.session_state.get("user_name", "User")
    logo_b64 = get_logo_base64()

    # Inject banner-specific CSS (offsets for fixed header)
    st.markdown(_BANNER_CSS, unsafe_allow_html=True)

    # Inject banner HTML
    st.markdown(
        f"""
        <div class="bc-header">
            <div style="display:flex;align-items:center;gap:12px;">
                <img src="data:image/png;base64,{logo_b64}"
                     style="height:38px;" alt="Logo">
                <span style="color:#fff;font-size:1.25em;font-weight:700;">
                    BC Health Platform
                </span>
            </div>
            <div style="display:flex;align-items:center;">
                <span style="color:rgba(255,255,255,0.9);font-size:0.9em;">
                    User: {user_name}
                </span>
                <a href="?logout=1" target="_self" class="logout-link">
                    Logout
                </a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
