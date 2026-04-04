# Sprint 3C: Healthcare Facility Finder
"""
BC Health Platform - Healthcare Facility Finder
Sprint 3C: Healthcare Facility Finder

Helps BC residents find nearby hospitals, walk-in clinics,
and urgent care centres using real facility data from the facilities CSV.
"""

import os
from datetime import datetime
from urllib.parse import quote

import pandas as pd
import folium
import streamlit as st
from streamlit_folium import st_folium

from components.auth import require_authentication


# =============================================================================
# PAGE PROTECTION — Must be logged in to view this page
# =============================================================================
require_authentication()


# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="CedarCare — Facility Finder",
    page_icon="🏥",
    layout="wide",
)

from components.header import render_header
render_header()


# =============================================================================
# DATA LOADING
# =============================================================================

@st.cache_data
def load_facilities() -> pd.DataFrame:
    csv_path = os.path.join(
        os.path.dirname(__file__), "../../data/facilities.csv"
    )
    df = pd.read_csv(csv_path)
    # Normalise types
    df["open_now"] = (
        df["open_now"].astype(str).str.strip().str.lower()
        .map({"true": True, "false": False})
        .fillna(False)
    )
    for col in ("rating", "distance_km", "latitude", "longitude"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


facilities_df = load_facilities()


# =============================================================================
# CONSTANTS & HELPERS
# =============================================================================

_TEAL_HEADER = (
    "background-color:#1a6b5c;color:white;padding:8px 16px;"
    "border-radius:4px;font-size:16px;font-weight:600;margin-bottom:12px;"
)

TYPE_COLOR = {
    "Hospital":      "#2196F3",
    "Walk-In Clinic": "#4CAF50",
    "Urgent Care":   "#FF9800",
}

TYPE_ICON = {
    "Hospital":      "🏥",
    "Walk-In Clinic": "🏠",
    "Urgent Care":   "🚑",
}


def section_header(text: str) -> None:
    st.markdown(
        f'<div style="{_TEAL_HEADER}">{text}</div>',
        unsafe_allow_html=True,
    )


def _color(facility_type: str) -> str:
    return TYPE_COLOR.get(facility_type, "#607D8B")


def build_map(df: pd.DataFrame) -> folium.Map:
    """Build a Folium map centred on Vancouver with facility markers."""
    m = folium.Map(
        location=[49.2827, -123.1207],
        zoom_start=11,
        tiles="CartoDB positron",
    )

    # "You are here" pin
    folium.Marker(
        location=[49.2827, -123.1207],
        tooltip="📍 You are here",
        popup="You are here",
        icon=folium.Icon(color="red", icon="home", prefix="fa"),
    ).add_to(m)

    # One circle marker per facility
    for _, row in df.iterrows():
        lat, lon = row["latitude"], row["longitude"]
        if pd.isna(lat) or pd.isna(lon):
            continue
        color = _color(row["type"])
        open_label = "🟢 Open Now" if row["open_now"] else "🔴 Closed"
        popup_html = (
            f"<b>{row['name']}</b><br>"
            f"<i>{row['type']}</i><br>"
            f"📍 {row['address']}<br>"
            f"📞 {row['phone']}<br>"
            f"⭐ {row['rating']}<br>"
            f"{open_label}"
        )
        folium.CircleMarker(
            location=[lat, lon],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=row["name"],
        ).add_to(m)
    return m


def facility_card(row: pd.Series) -> str:
    """Return an HTML facility card string for one facility row."""
    t = row["type"]
    color = _color(t)
    icon = TYPE_ICON.get(t, "🏥")

    if row["open_now"]:
        badge = (
            '<span style="background:#e8f5e9;color:#2e7d32;padding:2px 8px;'
            'border-radius:12px;font-size:0.78em;font-weight:600;">Open Now</span>'
        )
    else:
        badge = (
            '<span style="background:#f5f5f5;color:#757575;padding:2px 8px;'
            'border-radius:12px;font-size:0.78em;font-weight:600;">Closed</span>'
        )

    maps_url = (
        "https://www.google.com/maps/search/?api=1&query="
        + quote(f"{row['address']}, {row['city']}, BC")
    )
    tel_url = f"tel:{row['phone'].replace('-', '').replace(' ', '')}"

    return f"""
<div style="background:white;border:1px solid #e0e0e0;border-radius:8px;
  padding:16px;margin-bottom:10px;">
  <div style="display:flex;align-items:flex-start;gap:12px;margin-bottom:10px;">
    <div style="background:{color}22;color:{color};border-radius:8px;
      padding:8px 10px;font-size:1.4em;flex-shrink:0;">{icon}</div>
    <div style="flex:1;min-width:0;">
      <div style="font-weight:700;font-size:0.97em;color:#1a1a1a;
        white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{row['name']}</div>
      <div style="color:#555;font-size:0.83em;margin-top:3px;">
        📍 {row['address']}, {row['city']}</div>
      <div style="display:flex;align-items:center;gap:8px;margin-top:5px;flex-wrap:wrap;">
        <span style="font-size:0.83em;">⭐ {row['rating']:.1f}</span>
        <span style="color:#bbb;">•</span>
        <span style="font-size:0.82em;color:#666;">{row['distance_km']:.1f} km away</span>
        {badge}
      </div>
    </div>
  </div>
  <div style="display:flex;gap:8px;">
    <a href="{maps_url}" target="_blank"
      style="flex:1;display:inline-block;text-align:center;padding:7px 0;
        border:1.5px solid #1a6b5c;border-radius:6px;color:#1a6b5c;
        background:white;text-decoration:none;font-size:0.84em;font-weight:600;">
      🧭 Directions
    </a>
    <a href="{tel_url}"
      style="flex:1;display:inline-block;text-align:center;padding:7px 0;
        border:none;border-radius:6px;color:white;background:{color};
        text-decoration:none;font-size:0.84em;font-weight:600;">
      📞 Call
    </a>
  </div>
</div>"""


# =============================================================================
# PAGE HEADER
# =============================================================================

st.markdown("""
<div style="background:#fff;border-bottom:1px solid #e0edf4;
padding:16px 24px;display:flex;align-items:center;gap:16px;
margin:-1rem -1rem 1rem -1rem;">
    <div style="width:52px;height:52px;background:#faeeda;
    border-radius:12px;display:flex;align-items:center;
    justify-content:center;flex-shrink:0;">
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
            <path d="M14 4C10.13 4 7 7.13 7 11C7 16.25 14 24 14 24
            C14 24 21 16.25 21 11C21 7.13 17.87 4 14 4Z"
            fill="#EF9F27" stroke="#854F0B" stroke-width="1.2"/>
            <circle cx="14" cy="11" r="3" fill="#fff"
            stroke="#854F0B" stroke-width="1.2"/>
        </svg>
    </div>
    <div>
        <div style="font-size:1.8rem;font-weight:700;color:#1a1a1a;
        letter-spacing:-0.3px;">BC Healthcare Facility Finder</div>
        <div style="font-size:13px;color:#7a9aaa;margin-top:3px;">
            Find hospitals, clinics and urgent care centres near you
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# =============================================================================
# 2B — EMERGENCY CONTACTS
# =============================================================================

section_header("🚨 Emergency Contacts")

ec1, ec2, ec3 = st.columns(3)

with ec1:
    st.markdown("""
    <div style="background:#fff;border:0.5px solid #e0edf4;
    border-radius:12px;border-left:4px solid #dc2626;
    padding:20px;display:flex;align-items:center;gap:16px;">
        <div style="width:46px;height:46px;border-radius:50%;
        background:#fee2e2;display:flex;align-items:center;
        justify-content:center;flex-shrink:0;">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                <path d="M6.6 10.8c1.4 2.8 3.8 5.1 6.6 6.6l2.2-2.2
                c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20
                c0 .6-.4 1-1 1C10.6 21 3 13.4 3 4c0-.6.4-1 1-1h3.5
                c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1
                L6.6 10.8z" fill="#dc2626"/>
            </svg>
        </div>
        <div>
            <div style="font-size:13px;color:#555;font-weight:500;
            margin-bottom:5px;">Emergency Services</div>
            <div style="font-size:1.8rem;font-weight:700;color:#dc2626;
            letter-spacing:-1px;line-height:1;margin-bottom:5px;">911</div>
            <div style="font-size:13px;color:#555;">
            Life-threatening emergencies</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with ec2:
    st.markdown("""
    <div style="background:#fff;border:0.5px solid #e0edf4;
    border-radius:12px;border-left:4px solid #0078AE;
    padding:20px;display:flex;align-items:center;gap:16px;">
        <div style="width:46px;height:46px;border-radius:50%;
        background:#D4EFFC;display:flex;align-items:center;
        justify-content:center;flex-shrink:0;">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                <path d="M6.6 10.8c1.4 2.8 3.8 5.1 6.6 6.6l2.2-2.2
                c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20
                c0 .6-.4 1-1 1C10.6 21 3 13.4 3 4c0-.6.4-1 1-1h3.5
                c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1
                L6.6 10.8z" fill="#0078AE"/>
            </svg>
        </div>
        <div>
            <div style="font-size:13px;color:#555;font-weight:500;
            margin-bottom:5px;">HealthLink BC</div>
            <div style="font-size:1.8rem;font-weight:700;color:#0078AE;
            letter-spacing:-1px;line-height:1;margin-bottom:5px;">8-1-1</div>
            <div style="font-size:13px;color:#555;">
            24/7 health advice from nurses</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with ec3:
    st.markdown("""
    <div style="background:#fff;border:0.5px solid #e0edf4;
    border-radius:12px;border-left:4px solid #1D9E75;
    padding:20px;display:flex;align-items:center;gap:16px;">
        <div style="width:46px;height:46px;border-radius:50%;
        background:#e1f5ee;display:flex;align-items:center;
        justify-content:center;flex-shrink:0;">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                <path d="M6.6 10.8c1.4 2.8 3.8 5.1 6.6 6.6l2.2-2.2
                c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20
                c0 .6-.4 1-1 1C10.6 21 3 13.4 3 4c0-.6.4-1 1-1h3.5
                c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1
                L6.6 10.8z" fill="#1D9E75"/>
            </svg>
        </div>
        <div>
            <div style="font-size:13px;color:#555;font-weight:500;
            margin-bottom:5px;">Crisis Line</div>
            <div style="font-size:1.3rem;font-weight:700;color:#1D9E75;
            letter-spacing:-0.5px;line-height:1;margin-bottom:5px;">
            1-800-784-2433</div>
            <div style="font-size:13px;color:#555;">
            Mental health support</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# 2C — SEARCH FACILITIES
# =============================================================================

section_header("🔍 Search Facilities")

# Initialise search results in session state
if "ff_results" not in st.session_state:
    st.session_state.ff_results = facilities_df.copy()

fc1, fc2, fc3, fc4, fc5 = st.columns([2, 2, 2, 1, 2])

with fc1:
    type_options = ["All Types", "Hospital", "Walk-In Clinic", "Urgent Care"]
    selected_type = st.selectbox(
        "Facility Type", type_options, label_visibility="collapsed"
    )

with fc2:
    region_options = ["All Regions"] + sorted(
        facilities_df["region"].dropna().unique().tolist()
    )
    selected_region = st.selectbox(
        "Region", region_options, label_visibility="collapsed"
    )

with fc3:
    if selected_region == "All Regions":
        city_pool = facilities_df
    else:
        city_pool = facilities_df[facilities_df["region"] == selected_region]
    city_options = ["All Cities"] + sorted(city_pool["city"].dropna().unique().tolist())
    selected_city = st.selectbox(
        "City", city_options, label_visibility="collapsed"
    )

with fc4:
    open_now_toggle = st.toggle("Open Now Only")

with fc5:
    search_clicked = st.button("🔍 Search", use_container_width=True, type="primary")

if search_clicked:
    filtered = facilities_df.copy()
    if selected_type != "All Types":
        filtered = filtered[filtered["type"] == selected_type]
    if selected_region != "All Regions":
        filtered = filtered[filtered["region"] == selected_region]
    if selected_city != "All Cities":
        filtered = filtered[filtered["city"] == selected_city]
    if open_now_toggle:
        filtered = filtered[filtered["open_now"] == True]
    st.session_state.ff_results = filtered.reset_index(drop=True)

display_df = st.session_state.ff_results


# =============================================================================
# 2D — INTERACTIVE MAP
# =============================================================================

section_header("🗺️ Interactive Map")

st_folium(build_map(display_df), width="100%", height=400)

st.markdown(
    "🔵 **Hospitals** &nbsp;&nbsp; 🟢 **Walk-In Clinics** &nbsp;&nbsp; 🟠 **Urgent Care**",
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)


# =============================================================================
# 2E — NEARBY FACILITIES
# =============================================================================

count = len(display_df)
near_hdr, _, sort_col, filter_col = st.columns([6, 1, 1, 1])

with near_hdr:
    section_header(f"📋 Nearby Facilities ({count} found)")
with sort_col:
    st.button("↕ Sort By", key="sort_btn", use_container_width=True)
with filter_col:
    st.button("▼ Filter", key="filter_btn", use_container_width=True)

if count == 0:
    st.info(
        "No facilities match your search criteria. "
        "Try adjusting your filters or clearing the region/city selection."
    )
else:
    rows = display_df.reset_index(drop=True)
    for i in range(0, len(rows), 2):
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(facility_card(rows.iloc[i]), unsafe_allow_html=True)
        with col_b:
            if i + 1 < len(rows):
                st.markdown(facility_card(rows.iloc[i + 1]), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# =============================================================================
# 2F — HEALTH TIPS & INFORMATION
# =============================================================================

section_header("💡 Health Tips & Information")

TIPS = [
    (
        "🕐", "When to Visit Emergency",
        "Visit the emergency department for severe chest pain, difficulty breathing, "
        "severe bleeding, loss of consciousness, or suspected stroke symptoms.",
    ),
    (
        "👤", "Walk-In Clinic vs Urgent Care",
        "Walk-in clinics handle minor illnesses and injuries. Urgent care centers treat "
        "more serious conditions that aren't life-threatening but need immediate attention.",
    ),
    (
        "📋", "What to Bring",
        "Always bring your BC Services Card, list of current medications, relevant medical "
        "history, and insurance information if applicable.",
    ),
    (
        "📞", "Call Ahead",
        "For walk-in clinics, call ahead to check wait times and confirm they can address "
        "your specific health concern before visiting.",
    ),
]

tip_left, tip_right = st.columns(2)
tip_cols = [tip_left, tip_right]

for i, (icon, title, body) in enumerate(TIPS):
    with tip_cols[i % 2]:
        st.markdown(f"""
<div style="background:#f0f7ff;border:1px solid #c8deff;border-radius:8px;
  padding:16px;margin-bottom:12px;">
  <div style="font-size:1em;font-weight:700;margin-bottom:6px;">{icon} {title}</div>
  <div style="color:#444;font-size:0.87em;line-height:1.55;">{body}</div>
</div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# =============================================================================
# 2G — UNDERSTANDING FACILITY TYPES
# =============================================================================

section_header("🏥 Understanding Facility Types")

FACILITY_TYPE_CARDS = [
    (
        "#2196F3", "🏥", "Hospitals",
        "Full-service medical facilities offering emergency care, surgery, diagnostic "
        "services, and specialized treatments. Open 24/7 for emergencies.",
        ["24/7 Emergency", "Surgery", "Specialists"],
        "#e3f2fd", "#1565c0",
    ),
    (
        "#FF9800", "🚑", "Urgent Care Centers",
        "For non-life-threatening conditions requiring immediate attention. Treat injuries, "
        "infections, and acute illnesses with extended hours.",
        ["Extended Hours", "X-Rays", "Lab Tests"],
        "#fff3e0", "#bf360c",
    ),
    (
        "#4CAF50", "🏠", "Walk-In Clinics",
        "Convenient care for minor illnesses and injuries without appointments. Perfect for "
        "cold, flu, minor cuts, and routine health concerns.",
        ["No Appointment", "Quick Service", "Prescriptions"],
        "#e8f5e9", "#1b5e20",
    ),
]

ft_left, ft_right = st.columns(2)
ft_cols = [ft_left, ft_right]

for i, (color, icon, name, desc, tags, tag_bg, tag_color) in enumerate(FACILITY_TYPE_CARDS):
    tag_pills = " ".join(
        f'<span style="background:{tag_bg};color:{tag_color};padding:2px 8px;'
        f'border-radius:12px;font-size:0.78em;margin-right:2px;">{t}</span>'
        for t in tags
    )
    with ft_cols[i % 2]:
        st.markdown(f"""
<div style="background:white;border:1px solid #e0e0e0;border-radius:8px;
  padding:18px;margin-bottom:12px;">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
    <div style="background:{color}22;color:{color};border-radius:8px;
      padding:8px 10px;font-size:1.4em;">{icon}</div>
    <strong style="font-size:0.97em;">{name}</strong>
  </div>
  <div style="color:#555;font-size:0.87em;line-height:1.5;margin-bottom:10px;">{desc}</div>
  <div>{tag_pills}</div>
</div>""", unsafe_allow_html=True)


# =============================================================================
# FOOTER
# =============================================================================

st.divider()
st.caption("CedarCare — AI-powered health guidance for British Columbians")

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
