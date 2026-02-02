# 9_main.py - Input Widgets Part 2
import streamlit as st
import pandas as pd

df = pd.read_csv("data/9_sample.csv")

# Multi-select (returns a LIST)
multiselect = st.multiselect(
    "Choose columns", 
    options=df.columns[1:], 
    default=["col2"],
    max_selections=2
)
st.write(multiselect)

# Slider
st.divider()
slider = st.slider("Pick a number", min_value=0.0, max_value=10.0, value=5.0, step=0.1)
st.write(slider)

# Text input
st.divider()
text_input = st.text_input("What's your name?", placeholder="John Doe")
st.write(f"Your name is {text_input}")

# Number input
st.divider()
num_input = st.number_input("Pick a number", min_value=0, max_value=10, value=0, step=1)
st.write(f"You picked {num_input}")

# Text area (multi-line)
st.divider()
txt_area = st.text_area("Message", height=200, placeholder="Write here")
st.write(txt_area)