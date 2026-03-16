"""
BC Health Platform - Health Education Library
Sprint 3D: Health Education Library with searchable articles,
category browsing, and links to official BC health resources.
"""

import json
import os
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
    page_title="Health Library - BC Health Platform",
    page_icon="📚",
    layout="wide",
)

from components.header import render_header
render_header()


# =============================================================================
# LOAD ARTICLES
# =============================================================================

@st.cache_data
def load_articles():
    json_path = os.path.join(
        os.path.dirname(__file__), "../../data/health_articles.json"
    )
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


articles = load_articles()


# =============================================================================
# CONSTANTS & HELPERS
# =============================================================================

_TEAL = "#1a6b5c"

CATEGORIES = [
    {"name": "Pain & Injury",          "icon": "🖐️", "bg": "#FFEBEE", "desc": "Information on managing pain and treating injuries"},
    {"name": "Cold & Flu",             "icon": "💊", "bg": "#E3F2FD", "desc": "Symptoms, treatment, and prevention tips"},
    {"name": "Medications",            "icon": "💊", "bg": "#F3E5F5", "desc": "Drug information and safe use guidelines"},
    {"name": "Prevention & Wellness",  "icon": "🏃", "bg": "#E8F5E9", "desc": "Healthy living and disease prevention"},
    {"name": "Mental Health",          "icon": "🧠", "bg": "#EDE7F6", "desc": "Support for mental wellness and conditions"},
    {"name": "Heart Health",           "icon": "❤️", "bg": "#FFEBEE", "desc": "Cardiovascular health and heart disease"},
    {"name": "Child Health",           "icon": "👶", "bg": "#FFF3E0", "desc": "Pediatric health and parenting resources"},
    {"name": "Emergency Care",         "icon": "🚑", "bg": "#E3F2FD", "desc": "When to seek emergency medical help"},
]

POPULAR_ICONS = {1: "🏥", 2: "🤕", 3: "🧠", 4: "❤️"}


def section_header(text: str) -> None:
    st.markdown(
        f'<div style="background-color:{_TEAL};color:white;padding:8px 16px;'
        f'border-radius:4px;font-size:16px;font-weight:600;margin-bottom:12px;">'
        f'{text}</div>',
        unsafe_allow_html=True,
    )


def badge_pill(label: str, color: str) -> str:
    return (
        f'<span style="background:{color}22;color:{color};padding:2px 10px;'
        f'border-radius:12px;font-size:0.78em;font-weight:600;">{label}</span>'
    )


# =============================================================================
# SESSION STATE
# =============================================================================

if "hl_search_query" not in st.session_state:
    st.session_state.hl_search_query = ""
if "hl_selected_category" not in st.session_state:
    st.session_state.hl_selected_category = None


# =============================================================================
# CUSTOM CSS
# =============================================================================

st.markdown("""
<style>
/* blue primary buttons */
button[data-testid="stBaseButton-primary"],
button[kind="primary"] {
    background-color: #1976D2 !important;
    border-color: #1976D2 !important;
    border-radius: 24px !important;
    font-weight: 600 !important;
}
button[data-testid="stBaseButton-primary"]:hover,
button[kind="primary"]:hover {
    background-color: #1565C0 !important;
    border-color: #1565C0 !important;
}

/* ---  Search section: light-blue background band  --- */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.search-band-marker) {
    background: #dceef5;
    border-radius: 12px;
    padding: 32px 0;
    margin-bottom: 24px;
}

/* ---  Search section: white card in the centre column  --- */
div[data-testid="column"]:has(.search-card-marker) > div[data-testid="stVerticalBlockBorderWrapper"] {
    background: white;
    border-radius: 12px;
    padding: 32px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)


# =============================================================================
# PAGE HEADER
# =============================================================================

st.markdown(
    '<div style="font-size:1.8rem;font-weight:700;margin-bottom:2px;">📚 Health Education Library</div>'
    '<div style="color:#888;font-size:0.95rem;margin-bottom:20px;">'
    'Evidence-based health information from HealthLinkBC</div>',
    unsafe_allow_html=True,
)


# =============================================================================
# SECTION 1 — FIND HEALTH INFORMATION (search bar)
# =============================================================================

POPULAR_SEARCHES = ["Headache", "Fever", "Back Pain", "Diabetes", "High Blood Pressure"]

# The blue-band background is applied via CSS targeting .search-band-marker
search_band = st.container()
with search_band:
    # Invisible marker so CSS :has() can identify this container
    st.markdown('<span class="search-band-marker"></span>', unsafe_allow_html=True)

    # Centre the card in a narrow middle column
    _pad_l, search_center, _pad_r = st.columns([1.5, 3, 1.5])

    with search_center:
        # Invisible marker so CSS :has() styles this column as the white card
        st.markdown('<span class="search-card-marker"></span>', unsafe_allow_html=True)

        st.markdown(
            '<h3 style="text-align:center;margin-top:0;">Find Health Information</h3>',
            unsafe_allow_html=True,
        )

        search_col, btn_col = st.columns([5, 1])
        with search_col:
            search_input = st.text_input(
                "Search health topics",
                value=st.session_state.hl_search_query,
                placeholder="Search health topics... (e.g., headache, fever, back pain)",
                label_visibility="collapsed",
                key="hl_search_input",
            )
        with btn_col:
            if st.button("🔍 Search", type="primary", use_container_width=True):
                st.session_state.hl_search_query = search_input
                st.rerun()

        # Popular search chips as clickable pill buttons
        st.markdown(
            '<span style="font-size:0.85rem;color:#666;">Popular searches:</span>',
            unsafe_allow_html=True,
        )
        chip_cols = st.columns(5)
        for i, term in enumerate(POPULAR_SEARCHES):
            with chip_cols[i]:
                if st.button(term, key=f"chip_{term}", use_container_width=True):
                    st.session_state.hl_search_query = term
                    st.rerun()


# =============================================================================
# SEARCH RESULTS BLOCK
# =============================================================================

search_query = st.session_state.hl_search_query.strip()

if search_query:
    q_lower = search_query.lower()
    search_results = [
        a for a in articles
        if q_lower in a["title"].lower()
        or q_lower in a["category"].lower()
        or q_lower in a["summary"].lower()
        or any(q_lower in t.lower() for t in a.get("tags", []))
    ]

    # Header row with result count and clear button
    res_header_col, clear_col = st.columns([5, 1])
    with res_header_col:
        st.markdown(
            f"### Search Results for '{search_query}' ({len(search_results)} articles found)"
        )
    with clear_col:
        if st.button("Clear Search", type="primary", use_container_width=True):
            st.session_state.hl_search_query = ""
            st.rerun()

    if not search_results:
        st.info(
            f"No articles found for '{search_query}'. "
            "Try a different term or browse by category below."
        )
    else:
        for row_start in range(0, len(search_results), 3):
            cols = st.columns(3)
            for j in range(3):
                idx = row_start + j
                if idx >= len(search_results):
                    break
                a = search_results[idx]
                with cols[j]:
                    st.markdown(
                        f'<div style="background:white;border:1px solid #e0e0e0;border-radius:8px;'
                        f'padding:16px;margin-bottom:12px;min-height:180px;">'
                        f'{badge_pill(a["category"], a["badge_color"])}'
                        f'<div style="font-weight:700;font-size:0.97em;margin-top:8px;">{a["title"]}</div>'
                        f'<div style="color:#666;font-size:0.85em;margin-top:6px;line-height:1.5;">'
                        f'{a["summary"]}</div>'
                        f'<div style="color:#999;font-size:0.78em;margin-top:8px;">⏱ {a["read_time"]}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    with st.expander("Read More →"):
                        st.markdown(a["content"])
                        st.markdown(
                            f'<a href="{a["source_url"]}" target="_blank" style="color:{_TEAL};'
                            f'font-weight:600;text-decoration:none;">Visit Source →</a>',
                            unsafe_allow_html=True,
                        )

    st.markdown("<br>", unsafe_allow_html=True)


# =============================================================================
# DEFAULT VIEW — BROWSE BY CATEGORY, POPULAR TOPICS, ALL ARTICLES
# =============================================================================

if not search_query:

    # =========================================================================
    # SECTION 2 — BROWSE BY CATEGORY
    # =========================================================================

    st.markdown("### Browse by Category")
    st.markdown(
        '<div style="color:#666;font-size:0.9rem;margin-bottom:14px;">'
        'Explore health topics organized by condition and specialty</div>',
        unsafe_allow_html=True,
    )

    # Row 1
    row1 = st.columns(4)
    # Row 2
    row2 = st.columns(4)

    for idx, cat in enumerate(CATEGORIES):
        col = row1[idx] if idx < 4 else row2[idx - 4]
        with col:
            selected = st.session_state.hl_selected_category == cat["name"]
            border_style = f"border:2px solid {_TEAL};" if selected else "border:1px solid #e0e0e0;"
            st.markdown(
                f'<div style="background:white;{border_style}border-radius:8px;'
                f'padding:16px;text-align:center;margin-bottom:4px;">'
                f'<div style="background:{cat["bg"]};width:52px;height:52px;border-radius:50%;'
                f'display:inline-flex;align-items:center;justify-content:center;font-size:1.5em;'
                f'margin-bottom:8px;">{cat["icon"]}</div>'
                f'<div style="font-weight:700;font-size:0.95em;">{cat["name"]}</div>'
                f'<div style="color:#888;font-size:0.8em;margin-top:4px;">{cat["desc"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            btn_label = "✓ Selected" if selected else "Select"
            if st.button(btn_label, key=f"cat_{cat['name']}", use_container_width=True):
                if selected:
                    st.session_state.hl_selected_category = None
                else:
                    st.session_state.hl_selected_category = cat["name"]
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================================================================
    # SECTION 3 — POPULAR TOPICS (IDs 1-4)
    # =========================================================================

    section_header("🔥 Popular Topics")

    popular = [a for a in articles if a["id"] in (1, 2, 3, 4)]
    popular.sort(key=lambda a: a["id"])

    pop_row1 = st.columns(2)
    pop_row2 = st.columns(2)
    pop_cols = [pop_row1[0], pop_row1[1], pop_row2[0], pop_row2[1]]

    for i, article in enumerate(popular):
        with pop_cols[i]:
            banner = article.get("banner_color", "#1565C0")
            icon = article.get("icon", POPULAR_ICONS.get(article["id"], "📄"))

            # Banner with icon
            st.markdown(
                f'<div style="background:{banner};border-radius:8px 8px 0 0;height:160px;'
                f'display:flex;align-items:center;justify-content:center;">'
                f'<span style="font-size:3.5em;color:rgba(255,255,255,0.85);">{icon}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # Card body
            st.markdown(
                f'<div style="background:white;border:1px solid #e0e0e0;border-top:none;'
                f'border-radius:0 0 8px 8px;padding:16px;margin-bottom:16px;">'
                f'{badge_pill(article["category"], article["badge_color"])}'
                f'<div style="font-weight:700;font-size:1.05em;margin-top:8px;">{article["title"]}</div>'
                f'<div style="color:#666;font-size:0.88em;margin-top:6px;line-height:1.5;">{article["summary"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            with st.expander("Read More →"):
                st.markdown(article["content"])
                st.markdown(
                    f'<a href="{article["source_url"]}" target="_blank" style="color:{_TEAL};'
                    f'font-weight:600;text-decoration:none;">Visit Source →</a>',
                    unsafe_allow_html=True,
                )

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================================================================
    # SECTION 4 — ALL ARTICLES (filterable by category)
    # =========================================================================

    filtered_articles = list(articles)
    sel_cat = st.session_state.hl_selected_category

    if sel_cat:
        filtered_articles = [a for a in filtered_articles if a["category"] == sel_cat]

    section_header(f"📋 All Articles ({len(filtered_articles)} found)")

    if sel_cat:
        filter_msg_col, clear_col = st.columns([5, 1])
        with filter_msg_col:
            st.markdown(f'Filters: Category: **{sel_cat}**')
        with clear_col:
            if st.button("Clear Filters", use_container_width=True):
                st.session_state.hl_selected_category = None
                st.rerun()

    if not filtered_articles:
        st.info(
            "No articles match your filter. Try a different category or clear your filters."
        )
    else:
        for row_start in range(0, len(filtered_articles), 3):
            cols = st.columns(3)
            for j in range(3):
                a_idx = row_start + j
                if a_idx >= len(filtered_articles):
                    break
                a = filtered_articles[a_idx]
                with cols[j]:
                    st.markdown(
                        f'<div style="background:white;border:1px solid #e0e0e0;border-radius:8px;'
                        f'padding:16px;margin-bottom:12px;min-height:180px;">'
                        f'{badge_pill(a["category"], a["badge_color"])}'
                        f'<div style="font-weight:700;font-size:0.97em;margin-top:8px;">{a["title"]}</div>'
                        f'<div style="color:#666;font-size:0.85em;margin-top:6px;line-height:1.5;">'
                        f'{a["summary"]}</div>'
                        f'<div style="color:#999;font-size:0.78em;margin-top:8px;">⏱ {a["read_time"]}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    with st.expander("Read More →"):
                        st.markdown(a["content"])
                        st.markdown(
                            f'<a href="{a["source_url"]}" target="_blank" style="color:{_TEAL};'
                            f'font-weight:600;text-decoration:none;">Visit Source →</a>',
                            unsafe_allow_html=True,
                        )

    st.markdown("<br>", unsafe_allow_html=True)


# =============================================================================
# SECTION 5 — OFFICIAL BC HEALTH RESOURCES
# =============================================================================

section_header("🔗 Official BC Health Resources")

RESOURCES = [
    {
        "name": "HealthLinkBC",
        "icon": "📞",
        "bg": "#006271",
        "desc": "Official health information for BC residents. Call 8-1-1 for 24/7 health advice from nurses",
        "url": "https://www.healthlinkbc.ca",
    },
    {
        "name": "BC Centre for Disease Control",
        "icon": "⚙️",
        "bg": "#1a6b5c",
        "desc": "Disease prevention and public health information for British Columbia residents",
        "url": "http://www.bccdc.ca",
    },
    {
        "name": "BC Health Services",
        "icon": "🏥",
        "bg": "#2E7D32",
        "desc": "Find health services in your area including hospitals, clinics, and specialists",
        "url": "https://www2.gov.bc.ca/gov/content/health",
    },
]

rc1, rc2, rc3 = st.columns(3)

for col, res in zip([rc1, rc2, rc3], RESOURCES):
    with col:
        st.markdown(
            f'<div style="background:white;border:1px solid #e0e0e0;border-radius:8px;'
            f'padding:20px;margin-bottom:12px;">'
            f'<div style="background:{res["bg"]};width:48px;height:48px;border-radius:10px;'
            f'display:inline-flex;align-items:center;justify-content:center;font-size:1.4em;'
            f'color:white;margin-bottom:12px;">{res["icon"]}</div>'
            f'<div style="font-weight:700;font-size:1em;margin-bottom:6px;">{res["name"]}</div>'
            f'<div style="color:#666;font-size:0.87em;line-height:1.5;margin-bottom:12px;">'
            f'{res["desc"]}</div>'
            f'<a href="{res["url"]}" target="_blank" style="color:{_TEAL};font-weight:600;'
            f'text-decoration:none;font-size:0.9em;">Visit Website →</a>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)


# =============================================================================
# FOOTER
# =============================================================================

st.markdown(
    '<div style="background:#f0f7ff;border-radius:8px;padding:20px;margin-top:20px;">'
    '<div style="font-size:0.88em;color:#555;line-height:1.7;">'
    'ℹ️ <strong>Information Source:</strong> Content adapted from HealthLinkBC.ca — '
    "British Columbia's trusted source for non-emergency health information. "
    "All information is reviewed by healthcare professionals and updated regularly. "
    "This platform provides general health information only."
    '</div>'
    '<div style="font-size:0.88em;color:#555;margin-top:10px;line-height:1.7;">'
    "⚠️ Always consult a healthcare provider for medical advice, diagnosis, or "
    "treatment specific to your condition."
    '</div></div>',
    unsafe_allow_html=True,
)
