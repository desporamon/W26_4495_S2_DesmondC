# 6_main.py - Data Display Demo
import streamlit as st
import pandas as pd

# Read CSV file
df = pd.read_csv("data/6_sample.csv", dtype="int")

# Interactive dataframe - user can sort/filter
st.dataframe(df)

# st.write also works for dataframes
st.write(df)

# Static table - no interaction
st.table(df)

# Metric - great for dashboards/KPIs
st.metric(
    label="Expenses",
    value=900,
    delta=20,
    delta_color="inverse"
)