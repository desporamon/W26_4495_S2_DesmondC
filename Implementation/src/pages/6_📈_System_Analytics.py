"""
BC Health Platform - System Analytics Dashboard
Reads from synthetic_assessments.csv and displays platform-wide
health assessment insights, KPIs, and trends.
"""

import os

import pandas as pd
import streamlit as st
from components.auth import require_authentication


# =============================================================================
# PAGE PROTECTION
# =============================================================================
require_authentication()


# =============================================================================
# PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="System Analytics - BC Health Platform",
    page_icon="📈",
    layout="wide",
)

from components.header import render_header
render_header()


# =============================================================================
# SESSION STATE
# =============================================================================
if "sa_date_range" not in st.session_state:
    st.session_state.sa_date_range = "All Time"


# =============================================================================
# CSS — KPI cards + page styling
# =============================================================================

_TEAL = "#1a6b5c"

st.markdown("""
<style>
/* ---- teal section header ---- */
.sa-section-header {
    background-color: #1a6b5c;
    color: white;
    padding: 8px 16px;
    border-radius: 4px;
    font-size: 16px;
    font-weight: 700;
    letter-spacing: 0.01em;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)


# =============================================================================
# HELPERS
# =============================================================================

def section_header(text: str) -> None:
    st.markdown(f'<div class="sa-section-header">{text}</div>', unsafe_allow_html=True)


def kpi_card(icon: str, label: str, value: str, subtext: str) -> str:
    return (
        f'<div style="border:1px solid #e0e0e0;border-radius:8px;overflow:hidden;'
        f'background:white;box-shadow:0 2px 4px rgba(0,0,0,0.05);">'
        f'<div style="background:#1a6b5c;color:white;padding:8px 12px;'
        f'font-weight:600;font-size:14px;">{icon} {label}</div>'
        f'<div style="padding:16px;">'
        f'<div style="font-size:28px;font-weight:800;color:#1a1a1a;">{value}</div>'
        f'<div style="font-size:12px;color:#666;margin-top:4px;">{subtext}</div>'
        f'</div></div>'
    )


# =============================================================================
# DATA LOADING
# =============================================================================

@st.cache_data
def load_assessments():
    data_path = os.path.join(
        os.path.dirname(__file__), "../../data/synthetic_assessments.csv"
    )
    return pd.read_csv(data_path, parse_dates=["assessment_date"])


try:
    raw_df = load_assessments()
except FileNotFoundError:
    st.error(
        "Could not find **synthetic_assessments.csv**. "
        "Please run `python Implementation/src/data/generate_synthetic_data.py` first "
        "to generate the dataset."
    )
    st.stop()


# =============================================================================
# PAGE HEADER + DATE RANGE SELECTOR
# =============================================================================

header_left, header_right = st.columns([3, 2])

with header_left:
    st.markdown(
        '<div style="font-size:1.8rem;font-weight:700;margin-bottom:2px;">'
        '📈 System Analytics Dashboard</div>'
        '<div style="color:#888;font-size:0.95rem;margin-bottom:16px;">'
        'Platform-wide health assessment insights and trends</div>',
        unsafe_allow_html=True,
    )

with header_right:
    r_spacer, r_export, r_range = st.columns([1, 1.2, 1.5])
    with r_export:
        if st.button("Export Report", use_container_width=True):
            st.toast("Export feature coming soon!")
    with r_range:
        date_options = ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"]
        st.session_state.sa_date_range = st.selectbox(
            "Date range",
            date_options,
            index=date_options.index(st.session_state.sa_date_range),
            label_visibility="collapsed",
            key="sa_date_range_select",
        )


# =============================================================================
# APPLY DATE FILTER
# =============================================================================

max_date = raw_df["assessment_date"].max()

_range_days = {
    "Last 7 Days": 7,
    "Last 30 Days": 30,
    "Last 90 Days": 90,
}

if st.session_state.sa_date_range in _range_days:
    cutoff = max_date - pd.Timedelta(days=_range_days[st.session_state.sa_date_range])
    df = raw_df[raw_df["assessment_date"] > cutoff].copy()
else:
    df = raw_df.copy()


# =============================================================================
# KPI CARDS
# =============================================================================

total_users = df["patient_id"].nunique()

week_cutoff = max_date - pd.Timedelta(days=7)
active_this_week = df.loc[df["assessment_date"] > week_cutoff, "patient_id"].nunique()

total_assessments = len(df)

avg_duration_min = df["assessment_duration_seconds"].mean() / 60

kpi_cols = st.columns(4)

kpi_data = [
    ("✅", "Total Users", f"{total_users:,}", "200 registered patients"),
    ("👤", "Active This Week", f"{active_this_week:,}", "Unique patients, last 7 days"),
    ("📋", "Total Assessments", f"{total_assessments:,}", max_date.strftime("%b %d, %Y")),
    ("⏱️", "Avg Assessment Time", f"{avg_duration_min:.1f} min", "Average across all assessments"),
]

for col, (icon, label, value, sub) in zip(kpi_cols, kpi_data):
    with col:
        st.markdown(kpi_card(icon, label, value, sub), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
