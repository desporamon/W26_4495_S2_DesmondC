"""
BC Health Platform - My Personal Health Dashboard
Rebuilt to match finalized UI mockup with data-driven visualizations.

Sections:
  1. Page header with Export / New Assessment buttons
  2. Four summary stat cards (Total Checks, This Month, Most Common, Avg Urgency)
  3. Symptom Trends Over Time (Plotly area chart) with date filter
  4. Symptoms Breakdown donut chart + Assessment History table
  5. Footer
"""

import streamlit as st
import csv
import io
from datetime import date, datetime, timedelta
from collections import Counter, OrderedDict
import numpy as np
import plotly.graph_objects as go

from components.auth import require_authentication


# =============================================================================
# PAGE PROTECTION
# =============================================================================
require_authentication()


# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="My Dashboard - BC Health Platform",
    page_icon="\U0001f4ca",
    layout="wide"
)

from components.header import render_header
render_header()

from components.database import get_user_assessments



# =============================================================================
# HELPERS
# =============================================================================

URGENCY_SCORES = {"Self-Care": 1, "Routine": 2, "Urgent": 3, "Emergency": 4}

URGENCY_BADGES = {
    "Self-Care": {"label": "Home Care",     "cls": "badge-green",  "icon": "\u2713"},
    "Routine":   {"label": "Walk-in Clinic", "cls": "badge-yellow", "icon": "\u25cf"},
    "Urgent":    {"label": "Urgent Care",    "cls": "badge-orange", "icon": "\u25cf"},
    "Emergency": {"label": "Emergency",      "cls": "badge-red",    "icon": "\u25b2"},
}

FILTER_KEY = "dash_date_filter"
FILTER_OPTIONS = ["All Time", "Last 6 Months", "Last 3 Months", "Last Year"]

URGENCY_FILTER_KEY = "dash_urgency_filter"
URGENCY_FILTER_OPTIONS = ["All Urgency Levels", "Emergency", "Urgent", "Routine", "Self-Care"]


def parse_dt(dt_str):
    """Parse a 'YYYY-MM-DD HH:MM:SS' string into a datetime object."""
    try:
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return None


def get_primary_symptom(assessment):
    """Return the first extracted symptom (capitalized), or truncated raw text."""
    extracted = assessment.get("extracted_symptoms")
    if extracted and len(extracted) > 0:
        return extracted[0].capitalize()
    text = assessment.get("symptoms", "Assessment")
    return (text[:25] + "...") if len(text) > 25 else text


def format_date_long(dt_str):
    """Format datetime string as 'Mar 02, 2026'."""
    dt = parse_dt(dt_str)
    if not dt:
        return ""
    return f"{dt.strftime('%b')} {dt.day:02d}, {dt.year}"


def generate_report_csv(assessments):
    """Generate a CSV string from a list of assessment dicts."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Date", "Symptom", "Urgency Level", "Recommendation"])
    for a in assessments:
        writer.writerow([
            a.get("created_at", ""),
            get_primary_symptom(a),
            a.get("urgency_level", ""),
            a.get("recommendation", ""),
        ])
    return buf.getvalue()


# =============================================================================
# CUSTOM CSS
# =============================================================================

st.markdown("""
<style>
/* -- Rounded bordered containers -- */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 14px !important;
    overflow: hidden;
}
div[data-testid="stVerticalBlockBorderWrapper"] > div {
    border-radius: 14px !important;
}

/* -- Primary button (teal pill) -- */
button[data-testid="stBaseButton-primary"],
button[kind="primary"] {
    background-color: #1a6b5c !important;
    border-color: #1a6b5c !important;
    border-radius: 24px !important;
    font-weight: 600 !important;
    padding: 8px 20px !important;
    height: 42px !important;
}
button[data-testid="stBaseButton-primary"]:hover,
button[kind="primary"]:hover {
    background-color: #145a4c !important;
    border-color: #145a4c !important;
}

/* -- Download / secondary button (outlined pill) -- */
button[data-testid="stBaseButton-secondary"],
[data-testid="stDownloadButton"] button {
    border-radius: 24px !important;
    font-weight: 600 !important;
    padding: 8px 20px !important;
    height: 42px !important;
}

/* -- HTML "New Assessment" button (pure CSS, no Streamlit override issues) -- */
.new-assess-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 42px;
    background-color: #1a6b5c;
    color: #fff !important;
    border-radius: 24px;
    font-weight: 600;
    font-size: 14px;
    text-decoration: none !important;
    border: none;
    cursor: pointer;
    box-sizing: border-box;
    transition: background-color 0.2s;
}
.new-assess-btn:hover {
    background-color: #145a4c;
    color: #fff !important;
}

/* -- Stat card icon box -- */
.stat-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
}
.stat-icon-blue   { background: #dbeafe; color: #2563eb; }
.stat-icon-purple { background: #ede9fe; color: #7c3aed; }
.stat-icon-orange { background: #ffedd5; color: #ea580c; }
.stat-icon-green  { background: #d1fae5; color: #059669; }

/* -- Stat card typography -- */
.stat-value    { font-size: 28px; font-weight: 700; color: #1a1a1a; margin: 2px 0; }
.stat-subtitle { font-size: 13px; color: #666666; }

/* -- Status dot / arrow -- */
.status-indicator {
    width: 10px; height: 10px; border-radius: 50%; display: inline-block;
}

/* -- Assessment history table -- */
.hist-table {
    width: 100%;
    border-collapse: collapse;
}
.hist-table th {
    text-align: left;
    padding: 12px 8px;
    border-bottom: 2px solid #e0e0e0;
    font-weight: 600;
    color: #555;
    font-size: 14px;
}
.hist-table td {
    padding: 14px 8px;
    border-bottom: 1px solid #f0f0f0;
    font-size: 14px;
    color: #333;
}
.badge {
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    white-space: nowrap;
}
.badge-green  { background: #e8f5e9; color: #2e7d32; }
.badge-yellow { background: #fff3e0; color: #e65100; }
.badge-orange { background: #fff3e0; color: #e65100; }
.badge-red    { background: #ffebee; color: #c62828; }

/* -- Section header link -- */
.section-link {
    color: #1a6b5c;
    font-weight: 600;
    font-size: 14px;
    text-decoration: none;
}
.section-link:hover { color: #145a4c; text-decoration: underline; }

/* -- Empty-state -- */
.empty-msg {
    color: #999;
    font-size: 14px;
    padding: 30px 0;
    text-align: center;
}

/* -- Footer -- */
.dash-footer {
    text-align: center;
    color: #999;
    font-size: 12px;
    padding: 20px 0;
    border-top: 1px solid #e0e0e0;
    margin-top: 32px;
}
.dash-footer a { color: #888; text-decoration: none; margin: 0 8px; }
.dash-footer a:hover { color: #1a6b5c; }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# FETCH & FILTER DATA
# =============================================================================

username = st.session_state.user_name
user_id = st.session_state.user_id

# Get ALL assessments (high limit covers virtually any user)
all_assessments = get_user_assessments(user_id, limit=5000)

# Read the date-filter value (may already be in session_state from a prior run)
date_filter = st.session_state.get(FILTER_KEY, FILTER_OPTIONS[0])

now = datetime.now()

if date_filter == "Last 3 Months":
    cutoff = now - timedelta(days=90)
elif date_filter == "Last 6 Months":
    cutoff = now - timedelta(days=180)
elif date_filter == "Last Year":
    cutoff = now - timedelta(days=365)
else:
    cutoff = None

if cutoff:
    filtered = [a for a in all_assessments if (parse_dt(a["created_at"]) or datetime.min) >= cutoff]
else:
    filtered = list(all_assessments)

# Apply urgency filter (additive on top of date filter)
urgency_filter = st.session_state.get(URGENCY_FILTER_KEY, URGENCY_FILTER_OPTIONS[0])
if urgency_filter != "All Urgency Levels":
    filtered = [a for a in filtered if a.get("urgency_level") == urgency_filter]


# =============================================================================
# COMPUTE STATS
# =============================================================================

# Last urgency level (from most recent assessment overall, not filtered)
if all_assessments:
    last_urgency = all_assessments[0].get("urgency_level", "No data yet") or "No data yet"
    last_check_dt = parse_dt(all_assessments[0]["created_at"])
    if last_check_dt:
        days_since = (date.today() - last_check_dt.date()).days
        days_since_label = f"{days_since} days"
    else:
        days_since_label = "\u2014"
else:
    last_urgency = "No data yet"
    days_since_label = "\u2014"

# Most common primary symptom
symptom_counter = Counter()
for a in filtered:
    symptom_counter[get_primary_symptom(a)] += 1

if symptom_counter:
    most_common_symptom, most_common_count = symptom_counter.most_common(1)[0]
    total_filtered = len(filtered)
    most_common_pct = round(most_common_count / total_filtered * 100) if total_filtered else 0
else:
    most_common_symptom = "--"
    most_common_count = 0
    most_common_pct = 0

# Average urgency
urgency_values = [
    URGENCY_SCORES.get(a.get("urgency_level", "Self-Care"), 1)
    for a in filtered if a.get("urgency_level")
]
if urgency_values:
    avg_urg = sum(urgency_values) / len(urgency_values)
    if avg_urg >= 3.5:
        urg_label, urg_sub, urg_dot_color = "Critical", "Needs immediate attention", "#d32f2f"
    elif avg_urg >= 2.5:
        urg_label, urg_sub, urg_dot_color = "High", "Monitor closely", "#ff9800"
    elif avg_urg >= 1.5:
        urg_label, urg_sub, urg_dot_color = "Moderate", "Moderate health status", "#ff9800"
    else:
        urg_label, urg_sub, urg_dot_color = "Low", "Good health status", "#4caf50"
else:
    urg_label, urg_sub, urg_dot_color = "--", "No data yet", "#ccc"


# =============================================================================
# 1. PAGE HEADER
# =============================================================================

head_left, btn_export, btn_new = st.columns([5, 1.5, 1.5], vertical_alignment="bottom")

with head_left:
    logo_col, title_col = st.columns([0.5, 5])
    with logo_col:
        st.image("assets/logo.png", width=55)
    with title_col:
        st.markdown(
            '<div style="border-bottom: 2px solid #e0e0e0; padding-bottom: 12px; margin-bottom: 20px;">'
            '<span style="font-size: 1.5rem; font-weight: 700;">My Personal Health Dashboard</span><br>'
            f'<span style="font-size: 14px; color: #888;">Welcome back, {username}! Here\'s an overview of your health journey.</span>'
            '</div>',
            unsafe_allow_html=True,
        )

with btn_export:
    st.markdown('<div style="border-bottom: 2px solid #e0e0e0; padding-bottom: 12px; margin-bottom: 20px;">', unsafe_allow_html=True)
    st.download_button(
        label="\u2913 Export Report",
        data=generate_report_csv(all_assessments),
        file_name="health_report.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

with btn_new:
    st.markdown('<div style="border-bottom: 2px solid #e0e0e0; padding-bottom: 12px; margin-bottom: 20px;">', unsafe_allow_html=True)
    if st.button("+ New Assessment", type="primary", use_container_width=True):
        st.switch_page("pages/2_\U0001f4ac_Symptom_Assessment.py")
    st.markdown('</div>', unsafe_allow_html=True)


# =============================================================================
# 2. FOUR SUMMARY STAT CARDS
# =============================================================================

c1, c2, c3, c4 = st.columns(4, gap="medium")

with c1:
    with st.container(border=True):
        st.markdown(f"""
        <div style="background-color:#1a6b5c;color:white;padding:8px 16px;border-radius:4px 4px 0 0;font-size:14px;font-weight:600;margin:-1px -1px 14px -1px;box-shadow:0 2px 8px rgba(0,0,0,0.08);">\u26a0 Last Urgency Level</div>
        <div class="stat-value">{last_urgency}</div>
        <div class="stat-subtitle">Most recent assessment</div>
        """, unsafe_allow_html=True)

with c2:
    with st.container(border=True):
        st.markdown(f"""
        <div style="background-color:#1a6b5c;color:white;padding:8px 16px;border-radius:4px 4px 0 0;font-size:14px;font-weight:600;margin:-1px -1px 14px -1px;box-shadow:0 2px 8px rgba(0,0,0,0.08);">\U0001f4c5 Days Since Last Check</div>
        <div class="stat-value">{days_since_label}</div>
        <div class="stat-subtitle">Time since last assessment</div>
        """, unsafe_allow_html=True)

with c3:
    with st.container(border=True):
        st.markdown(f"""
        <div style="background-color:#1a6b5c;color:white;padding:8px 16px;border-radius:4px 4px 0 0;font-size:14px;font-weight:600;margin:-1px -1px 14px -1px;box-shadow:0 2px 8px rgba(0,0,0,0.08);">\U0001f9e0 Most Common</div>
        <div class="stat-value">{most_common_symptom}</div>
        <div class="stat-subtitle">{most_common_pct}% of assessments</div>
        """, unsafe_allow_html=True)

with c4:
    with st.container(border=True):
        st.markdown(f"""
        <div style="background-color:#1a6b5c;color:white;padding:8px 16px;border-radius:4px 4px 0 0;font-size:14px;font-weight:600;margin:-1px -1px 14px -1px;box-shadow:0 2px 8px rgba(0,0,0,0.08);">\u26a0 Avg Urgency</div>
        <div class="stat-value">{urg_label}</div>
        <div class="stat-subtitle">{urg_sub}</div>
        """, unsafe_allow_html=True)


# =============================================================================
# 3. SYMPTOM TRENDS OVER TIME  (Plotly area chart + date filter)
# =============================================================================

trend_left, urgency_col, date_col = st.columns([3, 1, 1], vertical_alignment="bottom")

with trend_left:
    st.markdown(
        '<div style="background-color: #1a6b5c; color: white; padding: 8px 16px; border-radius: 4px; font-size: 16px; font-weight: 600; margin-bottom: 12px;">📈 Symptom Trends Over Time</div>',
        unsafe_allow_html=True,
    )

with urgency_col:
    st.selectbox(
        "Urgency level",
        URGENCY_FILTER_OPTIONS,
        key=URGENCY_FILTER_KEY,
        label_visibility="collapsed",
    )

with date_col:
    date_filter = st.selectbox(
        "Date range",
        FILTER_OPTIONS,
        key=FILTER_KEY,
        label_visibility="collapsed",
    )

# Determine how many months to show on the x-axis
if date_filter == "Last 3 Months":
    n_months = 3
elif date_filter == "Last 6 Months":
    n_months = 6
elif date_filter == "Last Year":
    n_months = 12
else:
    # All Time — from earliest assessment to now (min 6 months)
    if filtered:
        earliest = min((parse_dt(a["created_at"]) or now) for a in filtered)
        n_months = max((now.year - earliest.year) * 12 + now.month - earliest.month + 1, 1)
    else:
        n_months = 6

# Build ordered month buckets
month_labels = []
month_keys = []
y, m = now.year, now.month
for i in range(n_months - 1, -1, -1):
    tm = m - i
    ty = y
    while tm <= 0:
        tm += 12
        ty -= 1
    month_keys.append(f"{ty}-{tm:02d}")
    month_labels.append(datetime(ty, tm, 1).strftime("%b %Y"))

monthly_counts = OrderedDict((k, 0) for k in month_keys)
for a in filtered:
    dt = parse_dt(a["created_at"])
    if dt:
        key = f"{dt.year}-{dt.month:02d}"
        if key in monthly_counts:
            monthly_counts[key] += 1

counts = list(monthly_counts.values())

if any(c > 0 for c in counts):
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=month_labels,
        y=counts,
        name="Assessments",
        fill="tozeroy",
        fillcolor="rgba(26, 107, 92, 0.12)",
        line=dict(color="#1a6b5c", width=2.5),
        mode="lines+markers",
        marker=dict(size=7, color="#1a6b5c"),
        hovertemplate="%{x}: %{y} assessments<extra></extra>",
    ))
    if len(counts) >= 2:
        x_idx = np.arange(len(counts))
        slope, intercept = np.polyfit(x_idx, counts, 1)
        trend_y = slope * x_idx + intercept
        fig_trend.add_trace(go.Scatter(
            x=month_labels,
            y=trend_y,
            mode="lines",
            line=dict(color="#ff7f0e", width=2, dash="dash"),
            name="Trend",
            hovertemplate="%{x}: %{y:.1f} (trend)<extra></extra>",
        ))
    fig_trend.update_layout(
        xaxis=dict(tickfont=dict(size=12)),
        yaxis=dict(tickfont=dict(size=12), dtick=5, rangemode="tozero"),
        template="simple_white",
        height=350,
        margin=dict(l=30, r=30, t=10, b=40),
        plot_bgcolor="white",
        showlegend=False,
    )
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.markdown(
        '<div class="empty-msg">No assessment data for the selected period. '
        'Complete a symptom check to start tracking trends!</div>',
        unsafe_allow_html=True,
    )


# =============================================================================
# 4. TWO COLUMNS — Symptoms Breakdown (donut) + Assessment History (table)
# =============================================================================

chart_col, table_col = st.columns(2, gap="medium")

# ---- Left: Symptoms Breakdown ----
with chart_col:
    with st.container(border=True):
        st.markdown(
            '<div style="background-color: #1a6b5c; color: white; padding: 8px 16px; border-radius: 4px; font-size: 16px; font-weight: 600; margin-bottom: 12px;">🔬 Symptoms Breakdown</div>',
            unsafe_allow_html=True,
        )

        if symptom_counter:
            # Keep top symptoms, group rare ones as "Other"
            sorted_syms = symptom_counter.most_common()
            top_syms = OrderedDict()
            other_total = 0
            for sym, cnt in sorted_syms:
                if cnt <= 1 and len(top_syms) >= 3:
                    other_total += cnt
                else:
                    top_syms[sym] = cnt
            if other_total > 0:
                top_syms["Other"] = other_total

            donut_colors = ["#006271", "#1a6b5c", "#3aafa9", "#ff9800", "#90a4ae",
                            "#4db6ac", "#00897b", "#e0e0e0"]

            fig_donut = go.Figure(data=[go.Pie(
                labels=list(top_syms.keys()),
                values=list(top_syms.values()),
                hole=0.5,
                marker=dict(colors=donut_colors[:len(top_syms)]),
                textinfo="percent",
                textposition="inside",
                pull=[0.02] * len(top_syms),
                hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
            )])
            fig_donut.update_layout(
                showlegend=True,
                legend=dict(orientation="h", yanchor="top", y=-0.1,
                            xanchor="center", x=0.5, font=dict(size=12)),
                height=400,
                margin=dict(t=20, b=20, l=20, r=20),
            )
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.markdown(
                '<div class="empty-msg">No symptom data yet. '
                'Complete an assessment to see your breakdown!</div>',
                unsafe_allow_html=True,
            )

# ---- Right: Assessment History ----
if "dash_hist_expanded" not in st.session_state:
    st.session_state.dash_hist_expanded = False

with table_col:
    with st.container(border=True):
        st.markdown(
            '<div style="background-color: #1a6b5c; color: white; padding: 8px 16px; border-radius: 4px; font-size: 16px; font-weight: 600; margin-bottom: 4px;">📋 Assessment History</div>',
            unsafe_allow_html=True,
        )

        # "View All" / "Show Less" toggle
        _, toggle_col = st.columns([4, 1])
        with toggle_col:
            toggle_label = "Show Less" if st.session_state.dash_hist_expanded else "View All"
            if st.button(toggle_label, key="hist_toggle"):
                st.session_state.dash_hist_expanded = not st.session_state.dash_hist_expanded
                st.rerun()

        show_assessments = filtered if st.session_state.dash_hist_expanded else filtered[:5]

        if show_assessments:
            rows_html = ""
            for a in show_assessments:
                date_str = format_date_long(a["created_at"])
                symptom = get_primary_symptom(a)
                urgency = a.get("urgency_level", "Self-Care")
                badge = URGENCY_BADGES.get(urgency, URGENCY_BADGES["Self-Care"])

                rows_html += f"""
                <tr>
                    <td>{date_str}</td>
                    <td>{symptom}</td>
                    <td><span class="badge {badge['cls']}">{badge['icon']} {badge['label']}</span></td>
                </tr>"""

            st.markdown(f"""
            <table class="hist-table">
                <thead>
                    <tr><th>Date</th><th>Symptom</th><th>Result</th></tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
            """, unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="empty-msg">No assessments yet. '
                'Start by completing a symptom check!</div>',
                unsafe_allow_html=True,
            )


# =============================================================================
# 5. FOOTER
# =============================================================================

st.markdown(
    '<div class="dash-footer">'
    f'\u00a9 {now.year} BC Health Platform. All rights reserved.'
    '<br>'
    '<a href="#">Privacy Policy</a> | '
    '<a href="#">Terms of Service</a> | '
    '<a href="#">Contact Us</a> | '
    '<a href="#">Help</a>'
    '</div>',
    unsafe_allow_html=True,
)
