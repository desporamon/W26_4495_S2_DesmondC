"""
BC Health Platform - System Analytics Dashboard
Reads from synthetic_assessments.csv and displays platform-wide
health assessment insights, KPIs, and trends.
"""

import os
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from components.auth import require_authentication

try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    _HAS_SKLEARN = True
except ImportError:
    _HAS_SKLEARN = False


# =============================================================================
# PAGE PROTECTION
# =============================================================================
require_authentication()


# =============================================================================
# PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="CedarCare — System Analytics",
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

st.markdown("""
<div style="background:#fff;border-bottom:1px solid #e0edf4;
padding:16px 24px;display:flex;align-items:center;gap:16px;
margin:-1rem -1rem 1rem -1rem;">
    <div style="width:52px;height:52px;background:#e6f1fb;
    border-radius:12px;display:flex;align-items:center;
    justify-content:center;flex-shrink:0;">
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
            <circle cx="14" cy="14" r="9" stroke="#0078AE"
            stroke-width="1.5" fill="none"/>
            <path d="M14 14L14 6" stroke="#0078AE"
            stroke-width="1.5" stroke-linecap="round"/>
            <path d="M14 14L20 17" stroke="#185FA5"
            stroke-width="1.5" stroke-linecap="round"/>
            <circle cx="14" cy="14" r="2" fill="#0078AE"/>
        </svg>
    </div>
    <div>
        <div style="font-size:1.8rem;font-weight:700;color:#1a1a1a;
        letter-spacing:-0.3px;">System Analytics Dashboard</div>
        <div style="font-size:13px;color:#7a9aaa;margin-top:3px;">
            Platform-wide health assessment insights and trends
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

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


# =============================================================================
# SHARED CHART LAYOUT DEFAULTS
# =============================================================================

_CHART_LAYOUT = dict(
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(family="sans-serif"),
    margin=dict(t=30, b=30, l=20, r=20),
)


# =============================================================================
# CHART 1 — TOP SYMPTOMS BAR CHART (full width)
# =============================================================================

section_header("📊 Top Symptoms This Month")

st.markdown(
    '<div style="font-size:0.85em;color:#555;margin-bottom:8px;">'
    "\U0001f534 Serious/Chronic &nbsp;&nbsp; \U0001f7e1 Infectious &nbsp;&nbsp; "
    '\U0001f535 General</div>',
    unsafe_allow_html=True,
)

_SYMPTOM_COLOR = {
    "chest pain": "#dc3545",
    "shortness of breath": "#dc3545",
    "high blood pressure": "#dc3545",
    "diabetes symptoms": "#dc3545",
    "fever": "#ffc107",
    "runny nose": "#ffc107",
    "cough": "#ffc107",
    "sore throat": "#ffc107",
}
# Everything else defaults to blue (General)
_SYMPTOM_DEFAULT_COLOR = "#1976D2"

symptom_counts = (
    df["symptom"]
    .value_counts()
    .head(10)
    .sort_values()  # ascending so largest bar is at the top in horizontal
)

color_list = [
    _SYMPTOM_COLOR.get(s, _SYMPTOM_DEFAULT_COLOR) for s in symptom_counts.index
]

fig_symptoms = px.bar(
    x=symptom_counts.values,
    y=symptom_counts.index,
    orientation="h",
    text=symptom_counts.values,
    labels={"x": "Number of Assessments", "y": ""},
)
fig_symptoms.update_traces(
    marker_color=color_list,
    textposition="outside",
)
fig_symptoms.update_layout(
    **_CHART_LAYOUT,
    height=400,
    yaxis=dict(showgrid=False),
    xaxis=dict(title="Number of Assessments"),
)
st.plotly_chart(fig_symptoms, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)


# =============================================================================
# CHART 2 & 3 — URGENCY + HEALTH AUTHORITY DONUTS (side by side)
# =============================================================================

donut_left, donut_right = st.columns(2)

# ---- LEFT: Urgency Distribution ----
with donut_left:
    section_header("⚠️ Urgency Distribution")

    urgency_counts = df["urgency_level"].value_counts()
    urgency_order = ["Routine", "Moderate", "Urgent", "Emergency"]
    urgency_colors = {
        "Routine": "#28a745",
        "Moderate": "#ffc107",
        "Urgent": "#fd7e14",
        "Emergency": "#dc3545",
    }
    # Reindex to ensure consistent order
    urgency_counts = urgency_counts.reindex(urgency_order).fillna(0).astype(int)

    fig_urgency = px.pie(
        names=urgency_counts.index,
        values=urgency_counts.values,
        hole=0.4,
        color=urgency_counts.index,
        color_discrete_map=urgency_colors,
    )
    fig_urgency.update_traces(textinfo="percent", textposition="inside")
    fig_urgency.update_layout(
        **_CHART_LAYOUT,
        height=350,
        legend=dict(orientation="v", x=1.02, y=0.5),
    )
    st.plotly_chart(fig_urgency, use_container_width=True)

# ---- RIGHT: Usage by Health Authority ----
with donut_right:
    section_header("📍 Usage by Health Authority")

    city_to_ha = {
        "Surrey": "Fraser Health",
        "Abbotsford": "Fraser Health",
        "Vancouver": "Vancouver Coastal Health",
        "Burnaby": "Vancouver Coastal Health",
        "Richmond": "Vancouver Coastal Health",
        "Kelowna": "Interior Health",
        "Kamloops": "Interior Health",
        "Victoria": "Island Health",
        "Nanaimo": "Island Health",
        "Prince George": "Northern Health",
    }

    ha_counts = (
        df["city"]
        .map(city_to_ha)
        .value_counts()
    )

    ha_order = [
        "Fraser Health",
        "Vancouver Coastal Health",
        "Interior Health",
        "Island Health",
        "Northern Health",
    ]
    ha_colors = {
        "Fraser Health": "#1a6b5c",
        "Vancouver Coastal Health": "#2d9b87",
        "Interior Health": "#48c4a8",
        "Island Health": "#7dd8c6",
        "Northern Health": "#b3ece1",
    }
    ha_counts = ha_counts.reindex(ha_order).fillna(0).astype(int)

    fig_ha = px.pie(
        names=ha_counts.index,
        values=ha_counts.values,
        hole=0.4,
        color=ha_counts.index,
        color_discrete_map=ha_colors,
    )
    fig_ha.update_traces(textinfo="percent", textposition="inside")
    fig_ha.update_layout(
        **_CHART_LAYOUT,
        height=350,
        legend=dict(orientation="v", x=1.02, y=0.5),
    )
    st.plotly_chart(fig_ha, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)


# =============================================================================
# CHART 4 — ASSESSMENT TRENDS OVER TIME (full width)
# =============================================================================

section_header("📈 Assessment Trends Over Time")

# Group by month — use period to sort correctly then format labels
monthly = (
    df.assign(month_period=df["assessment_date"].dt.to_period("M"))
    .groupby("month_period")
    .size()
    .reset_index(name="count")
    .sort_values("month_period")
)
monthly["month_label"] = monthly["month_period"].dt.strftime("%b %Y")

# Numeric x-positions for trendline calculation
x_num = np.arange(len(monthly))
y_vals = monthly["count"].values

# Area + line trace
fig_trend = px.area(
    monthly,
    x="month_label",
    y="count",
    labels={"month_label": "", "count": "Assessment Count"},
)
fig_trend.update_traces(
    line=dict(color=_TEAL, width=2.5),
    fillcolor="rgba(26,107,92,0.12)",
)

# Trendline via numpy polyfit (degree 1)
coeffs = np.polyfit(x_num, y_vals, 1)
trend_y = np.polyval(coeffs, x_num)

fig_trend.add_trace(
    go.Scatter(
        x=monthly["month_label"],
        y=trend_y,
        mode="lines",
        name="Trend",
        line=dict(color="#ff7f0e", width=2, dash="dash"),
    )
)

# Annotate max and min data points
idx_max = int(np.argmax(y_vals))
idx_min = int(np.argmin(y_vals))

fig_trend.add_annotation(
    x=monthly["month_label"].iloc[idx_max],
    y=y_vals[idx_max],
    text=f"<b>{y_vals[idx_max]} — {monthly['month_label'].iloc[idx_max]}</b>",
    showarrow=True,
    arrowhead=2,
    ay=-30,
    font=dict(size=11),
)
fig_trend.add_annotation(
    x=monthly["month_label"].iloc[idx_min],
    y=y_vals[idx_min],
    text=f"<b>{y_vals[idx_min]} — {monthly['month_label'].iloc[idx_min]}</b>",
    showarrow=True,
    arrowhead=2,
    ay=30,
    font=dict(size=11),
)

fig_trend.update_layout(
    **_CHART_LAYOUT,
    height=400,
    showlegend=True,
    legend=dict(orientation="h", y=-0.15),
)
st.plotly_chart(fig_trend, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)


# =============================================================================
# K-MEANS CLUSTERING SECTION
# =============================================================================

section_header("🔬 Patient Cluster Analysis (K-Means)")

st.markdown(
    '<div style="color:#555;font-size:0.9rem;margin-bottom:14px;">'
    "Unsupervised K-Means clustering automatically groups patients by age and "
    "assessment patterns to identify natural health behaviour segments.</div>",
    unsafe_allow_html=True,
)

if not _HAS_SKLEARN:
    st.warning("scikit-learn not installed. Run: `pip install scikit-learn`")
    st.stop()

_SERIOUS_SYMPTOMS = {"chest pain", "shortness of breath", "high blood pressure", "diabetes symptoms"}

if df["patient_id"].nunique() < 10:
    st.info("Not enough data for clustering. Select a wider date range.")
else:
    # --- aggregate per patient ---
    patient_agg = df.groupby("patient_id").agg(
        mean_age=("age", "mean"),
        assessment_count=("patient_id", "size"),
        urgent_ratio=("urgency_level", lambda x: (x.isin(["Urgent", "Emergency"])).mean()),
        chronic_ratio=("symptom", lambda x: x.isin(_SERIOUS_SYMPTOMS).mean()),
    ).reset_index()

    # --- standardise & cluster ---
    features = ["mean_age", "assessment_count", "urgent_ratio", "chronic_ratio"]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(patient_agg[features])

    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    patient_agg["cluster"] = kmeans.fit_predict(X_scaled)

    # --- name clusters by combined chronic_ratio + urgent_ratio ---
    cluster_scores = (
        patient_agg.groupby("cluster")[["chronic_ratio", "urgent_ratio"]]
        .mean()
        .sum(axis=1)
        .sort_values(ascending=False)
    )
    _CLUSTER_NAMES = ["Chronic/Elderly Patients", "High-Risk Patients", "Healthy/Occasional Users"]
    cluster_name_map = {cid: name for cid, name in zip(cluster_scores.index, _CLUSTER_NAMES)}
    patient_agg["cluster_name"] = patient_agg["cluster"].map(cluster_name_map)

    _CLUSTER_COLORS = {
        "Chronic/Elderly Patients": "#dc3545",
        "High-Risk Patients": "#ffc107",
        "Healthy/Occasional Users": "#1976D2",
    }

    # --- scatter plot ---
    fig_cluster = px.scatter(
        patient_agg,
        x="assessment_count",
        y="urgent_ratio",
        color="cluster_name",
        size="mean_age",
        color_discrete_map=_CLUSTER_COLORS,
        hover_data=["mean_age", "assessment_count", "urgent_ratio", "chronic_ratio"],
        labels={
            "assessment_count": "Assessment Frequency",
            "urgent_ratio": "Urgent Case Ratio",
            "cluster_name": "Cluster",
            "mean_age": "Age",
        },
        title="Patient Segments by Assessment Frequency and Urgency Profile",
    )
    fig_cluster.update_layout(
        **_CHART_LAYOUT,
        height=450,
    )
    st.plotly_chart(fig_cluster, use_container_width=True)

    # --- summary cards ---
    cluster_cols = st.columns(3)
    for col, name in zip(cluster_cols, _CLUSTER_NAMES):
        grp = patient_agg[patient_agg["cluster_name"] == name]
        if grp.empty:
            continue
        with col:
            st.markdown(
                f'<div style="border:1px solid #e0e0e0;border-radius:8px;overflow:hidden;'
                f'background:white;box-shadow:0 2px 4px rgba(0,0,0,0.05);">'
                f'<div style="background:#1a6b5c;color:white;padding:8px 12px;'
                f'font-weight:600;font-size:14px;">{name}</div>'
                f'<div style="padding:16px;line-height:1.9;font-size:0.92em;">'
                f'<div>👥 {len(grp)} patients</div>'
                f'<div>🎂 Avg age: {grp["mean_age"].mean():.0f}</div>'
                f'<div>📋 Avg assessments: {grp["assessment_count"].mean():.1f}</div>'
                f'<div>⚠️ Urgent ratio: {grp["urgent_ratio"].mean() * 100:.1f}%</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

st.divider()
st.markdown(
    '<div style="text-align:center;color:#999;font-size:12px;padding:20px 0;margin-top:32px;">'
    f'\u00a9 {datetime.now().year} CedarCare. All rights reserved.'
    '<br>'
    '<a href="#" style="color:#888;text-decoration:none;margin:0 8px;">Privacy Policy</a> | '
    '<a href="#" style="color:#888;text-decoration:none;margin:0 8px;">Terms of Service</a> | '
    '<a href="#" style="color:#888;text-decoration:none;margin:0 8px;">Contact Us</a> | '
    '<a href="#" style="color:#888;text-decoration:none;margin:0 8px;">Help</a>'
    '</div>',
    unsafe_allow_html=True,
)
