# 11_main.py - Layout Demo
import streamlit as st
import pandas as pd

# Sidebar - left panel
with st.sidebar:
    st.write("Text in the sidebar")

# Columns - side by side
col1, col2, col3 = st.columns(3)

col1.write("Text in column 1")
slider = col2.slider("Choose a number", min_value=0, max_value=10)
col3.write(slider)

# Tabs - switch between views
df = pd.read_csv("data/11_sample.csv")

tab1, tab2 = st.tabs(["Line plot", "Bar plot"])

with tab1:
    tab1.write("A line plot")
    st.line_chart(df, x="year", y=["col1", "col2", "col3"])

with tab2:
    tab2.write("A bar plot")
    st.bar_chart(df, x="year", y=["col1", "col2", "col3"])

# Expander - collapsible section
with st.expander("Click to expand"):
    st.write("Hidden text that shows when expanded")

# Container
with st.container():
    st.write("Inside container")

st.write("Outside container")