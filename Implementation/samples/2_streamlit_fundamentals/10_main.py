# 10_main.py - Forms Demo
import streamlit as st

with st.form("form_key"):
    st.write("What would you like to order?")
    
    appetizer = st.selectbox("Appetizers", options=["choice1", "choice2", "choice3"])
    main = st.selectbox("Main course", options=["choice1", "choice2", "choice3"])
    dessert = st.selectbox("Dessert", options=["choice1", "choice2", "choice3"])
    
    wine = st.checkbox("Are you bringing wine?")
    visit_date = st.date_input("When are you coming?")
    visit_time = st.time_input("At what time?")
    allergies = st.text_area("Any allergies?", placeholder="Leave a note")
    
    submit_btn = st.form_submit_button("Submit")

st.write(f"""Your order:
Appetizer: {appetizer}
Main: {main}
Dessert: {dessert}
Bringing wine: {"yes" if wine else "no"}
Date: {visit_date}
Time: {visit_time}
Allergies: {allergies}
""")