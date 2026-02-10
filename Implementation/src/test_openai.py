# Temporary test file - delete after verification

import streamlit as st
from components.openai_utils import test_openai_connection, extract_symptoms

st.title("OpenAI API Test")

# Step 1: Test API connection
if test_openai_connection():
    st.success("API key is valid and connection is working!")
else:
    st.error("API connection failed. Check your OPENAI_API_KEY in secrets.toml.")

# Step 2: Test symptom extraction
result = extract_symptoms("I've had chest pain for 2 hours and feel dizzy")
st.subheader("Symptom Extraction Result")
st.json(result)
