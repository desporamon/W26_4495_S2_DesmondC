# 5_main.py - Text Elements Demo
import streamlit as st

# Title - biggest text
st.title("Your title")

# Header and Subheader
st.header("Main header")
st.subheader("This is a subheader")

# Markdown - supports **bold**, *italic*
st.markdown("This is markdown **text**")
st.markdown("# Header1")
st.markdown("## Header 2")

# Caption - small gray text
st.caption("This is a caption")

# Code block - syntax highlighted
st.code("""import pandas as pd
pd.read_csv(my_csv_file)
""")

# Plain text
st.text("Some text")

# LaTeX for math
st.latex("x = 2^2")

# Divider - horizontal line
st.text('Text above divider')
st.divider()
st.text('Text below divider')

# st.write - displays anything
st.write('Some text')