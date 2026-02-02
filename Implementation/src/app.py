import streamlit as st

# Page config
st.set_page_config(
    page_title="BC Health Platform",
    page_icon="🏥",
    layout="wide"
)

# Test if theme works
st.title("🏥 BC Health Platform")
st.write("Welcome! Your app is working!")

# Test sidebar
st.sidebar.success("✅ Sidebar working!")

# Test colors
st.info("If you see light cyan sidebar, theme is working!")