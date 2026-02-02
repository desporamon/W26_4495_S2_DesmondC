# 7_main.py - Charts Demo
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data/7_sample.csv")

# Line chart
st.line_chart(df, x="year", y=["col1", "col2", "col3"])

# Area chart
st.area_chart(df, x="year", y=["col1", "col2"])

# Bar chart (stacked by default)
st.bar_chart(df, x="year", y=["col1", "col2", "col3"])

# Map - needs latitude/longitude columns
geo_df = pd.read_csv("data/7_sample_map.csv")
st.map(geo_df)

# Matplotlib for more control
fig, ax = plt.subplots()
ax.plot(df.year, df.col1)
ax.set_title("My figure title")
ax.set_xlabel("x label")
ax.set_ylabel("y label")
fig.autofmt_xdate()

st.pyplot(fig)