"""
BC Health Platform - Home Page
Rebuilt to match finalized UI mockup with personalized dashboard.

Sections:
  1. Welcome header with username
  2. Quick Actions row (3 cards)
  3. My Health Summary + Recent Activity (2-column)
  4. BC Health Tip of the Day banner
"""

import streamlit as st
import random
from datetime import datetime

from components.auth import require_authentication


# =============================================================================
# PAGE PROTECTION - Must be logged in to view this page
# =============================================================================
require_authentication()


# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="CedarCare — Home",
    page_icon="🏠",
    layout="wide"
)

from components.header import render_header
render_header()

from components.database import get_user_assessments, get_assessment_stats


# =============================================================================
# HELPERS
# =============================================================================

def get_relative_time(dt_str):
    """Convert a datetime string to relative time like '2 days ago'."""
    if not dt_str:
        return "N/A"
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return "N/A"
    diff = datetime.now() - dt
    if diff.days == 0:
        hours = diff.seconds // 3600
        if hours == 0:
            minutes = diff.seconds // 60
            return f"{minutes} min ago" if minutes > 1 else "Just now"
        return f"{hours} hours ago" if hours > 1 else "1 hour ago"
    elif diff.days == 1:
        return "1 day ago"
    elif diff.days < 7:
        return f"{diff.days} days ago"
    elif diff.days < 30:
        weeks = diff.days // 7
        return f"{weeks} weeks ago" if weeks > 1 else "1 week ago"
    else:
        months = diff.days // 30
        return f"{months} months ago" if months > 1 else "1 month ago"


def format_date_short(dt_str):
    """Format datetime string as 'Jan 30'."""
    if not dt_str:
        return ""
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        return f"{dt.strftime('%b')} {dt.day}"
    except ValueError:
        return ""


def get_primary_condition(assessment):
    """Get the primary condition name from an assessment."""
    extracted = assessment.get("extracted_symptoms")
    if extracted and len(extracted) > 0:
        return extracted[0].capitalize()
    text = assessment.get("symptoms", "Assessment")
    return (text[:25] + "...") if len(text) > 25 else text


URGENCY_MAP = {
    "Self-Care": {"label": "Home care", "color": "#4caf50"},
    "Routine":   {"label": "Walk-in clinic", "color": "#ff9800"},
    "Urgent":    {"label": "Urgent care", "color": "#f44336"},
    "Emergency": {"label": "Emergency", "color": "#d32f2f"},
}

HEALTH_TIPS = [
    "Flu season is here! Get your free flu shot at any BC pharmacy. No appointment needed.",
    "HealthLinkBC (811) offers free health advice 24/7 in 130+ languages.",
    "BC residents can access mental health support through BounceBack \u2014 a free CBT program.",
    "Walk-in clinics in BC don't require appointments. Find one near you!",
    "BC PharmaCare may cover your prescription costs. Check if you're eligible.",
    "Regular hand washing is the most effective way to prevent the spread of illness.",
    "BC offers free cancer screenings. Talk to your doctor about which ones are right for you.",
]


# =============================================================================
# CUSTOM CSS
# =============================================================================

st.markdown("""
<style>
/* -- Rounded bordered containers (cards) -- */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 14px !important;
    overflow: hidden;
}
div[data-testid="stVerticalBlockBorderWrapper"] > div {
    border-radius: 14px !important;
}

/* -- Teal-colored page links -- */
[data-testid="stPageLink-NavLink"] {
    color: #1a6b5c !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}
[data-testid="stPageLink-NavLink"]:hover {
    color: #145a4c !important;
}

/* -- Primary button (teal, rounded pill) -- */
button[data-testid="stBaseButton-primary"] {
    background-color: #1a6b5c !important;
    border-color: #1a6b5c !important;
    border-radius: 24px !important;
    font-weight: 600 !important;
    padding: 8px 24px !important;
}
button[data-testid="stBaseButton-primary"]:hover {
    background-color: #145a4c !important;
    border-color: #145a4c !important;
}

/* -- Icon box in Quick Action cards -- */
.icon-box {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    margin-bottom: 4px;
}
.icon-blue  { background: #dbeafe; }
.icon-green { background: #d1fae5; }
.icon-teal  { background: #ccfbf1; }

/* -- Stat rows inside Health Summary card -- */
.stat-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid #f0f0f0;
    font-size: 15px;
}
.stat-row:last-of-type { border-bottom: none; }
.stat-label { color: #555; }
.stat-value { font-weight: 600; color: #1a1a1a; }

/* -- Recent Activity items -- */
.activity-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 10px 0;
}
.activity-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-top: 5px;
    flex-shrink: 0;
}
.activity-title {
    font-size: 15px;
    font-weight: 600;
    color: #1a1a1a;
}
.activity-rec {
    font-size: 13px;
    color: #888;
    margin-top: 2px;
}

/* -- Health tip banner background -- */
.tip-banner-bg {
    background: #eef8f6;
    border-radius: 14px;
    padding: 24px 28px;
}
.tip-header {
    font-size: 13px;
    font-weight: 800;
    color: #1a6b5c;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
}
.tip-text {
    font-size: 15px;
    color: #444;
}

/* -- Empty-state message -- */
.empty-msg {
    color: #999;
    font-size: 14px;
    padding: 20px 0;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)


# =============================================================================
# FETCH DATA
# =============================================================================

username = st.session_state.user_name
user_id = st.session_state.user_id

stats = get_assessment_stats(user_id)
recent = get_user_assessments(user_id, limit=3)

# Compute most-common symptom percentage
most_common_name = stats.get("most_common_symptom")
most_common_pct = 0
if most_common_name and stats["total_count"] > 0:
    mc_count = stats.get("most_common_symptom_count", 0)
    most_common_pct = round(mc_count / stats["total_count"] * 100) if mc_count else 0


# =============================================================================
# 1. WELCOME HEADER
# =============================================================================

st.markdown(f"## \U0001f44b Welcome back, {username}!")
st.caption("Here's your health overview")


# =============================================================================
# 2. QUICK ACTIONS ROW
# =============================================================================

qa1, qa2, qa3 = st.columns(3, gap="medium")

with qa1:
    with st.container(border=True):
        st.markdown('<div class="icon-box icon-blue">\U0001f4ac</div>', unsafe_allow_html=True)
        st.markdown("**Check Symptoms**")
        st.caption("Assess your symptoms now")
        st.page_link("pages/2_\U0001f4ac_Symptom_Assessment.py", label="Get Started \u2192")

with qa2:
    with st.container(border=True):
        st.markdown('<div class="icon-box icon-green">\U0001f4cd</div>', unsafe_allow_html=True)
        st.markdown("**Find Facility**")
        st.caption("Locate nearby clinics")
        st.page_link("pages/4_\U0001f5fa\ufe0f_Facility_Finder.py", label="Search Now \u2192")

with qa3:
    with st.container(border=True):
        st.markdown('<div class="icon-box icon-teal">\U0001f4da</div>', unsafe_allow_html=True)
        st.markdown("**Health Info**")
        st.caption("Browse health topics")
        st.page_link("pages/5_\U0001f4da_Health_Library.py", label="Explore \u2192")


# =============================================================================
# 3. HEALTH SUMMARY + RECENT ACTIVITY
# =============================================================================

sum_col, act_col = st.columns(2, gap="medium")

# ---- Left: My Health Summary ----
with sum_col:
    with st.container(border=True):
        st.markdown("**\U0001f6e1\ufe0f My Health Summary**")

        if stats["total_count"] > 0:
            last_check = get_relative_time(recent[0]["created_at"]) if recent else "N/A"
            mc_display = (
                f"{most_common_name.capitalize()} ({most_common_pct}%)"
                if most_common_name else "N/A"
            )

            st.markdown(f"""
            <div class="stat-row">
                <span class="stat-label">Total Assessments:</span>
                <span class="stat-value">{stats['total_count']}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Last Check:</span>
                <span class="stat-value">{last_check}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Most Common:</span>
                <span class="stat-value">{mc_display}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="empty-msg">No assessments yet. '
                'Start your first symptom check!</div>',
                unsafe_allow_html=True,
            )

        st.page_link("pages/3_\U0001f4ca_My_Dashboard.py", label="View Full Dashboard \u2192")

# ---- Right: Recent Activity ----
with act_col:
    with st.container(border=True):
        st.markdown("**\U0001f550 Recent Activity**")

        if recent:
            parts = []
            for a in recent:
                urgency = a.get("urgency_level", "Self-Care")
                info = URGENCY_MAP.get(urgency, URGENCY_MAP["Self-Care"])
                date_label = format_date_short(a["created_at"])
                condition = get_primary_condition(a)

                parts.append(f"""
                <div class="activity-item">
                    <div class="activity-dot" style="background:{info['color']};"></div>
                    <div>
                        <div class="activity-title">{date_label}: {condition}</div>
                        <div class="activity-rec">Recommendation: {info['label']}</div>
                    </div>
                </div>
                """)

            st.markdown("".join(parts), unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="empty-msg">No recent activity. '
                'Start by completing a symptom assessment!</div>',
                unsafe_allow_html=True,
            )


# =============================================================================
# 4. BC HEALTH TIP OF THE DAY
# =============================================================================

# Keep the tip stable within the session
if "health_tip_idx" not in st.session_state:
    st.session_state.health_tip_idx = random.randint(0, len(HEALTH_TIPS) - 1)

tip_text = HEALTH_TIPS[st.session_state.health_tip_idx]

tip_left, tip_right = st.columns([4, 1], vertical_alignment="center")

with tip_left:
    st.markdown(f"""
    <div class="tip-banner-bg">
        <div class="tip-header">\U0001f4a1 BC HEALTH TIP OF THE DAY</div>
        <div class="tip-text">{tip_text}</div>
    </div>
    """, unsafe_allow_html=True)

with tip_right:
    if st.button("Find Nearest Pharmacy \u2192", type="primary", use_container_width=True):
        st.switch_page("pages/4_\U0001f5fa\ufe0f_Facility_Finder.py")
