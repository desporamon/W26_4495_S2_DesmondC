# 12_main.py - Capstone: Canada Population Dashboard
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load data from URL (no CSV file needed!)
URL = "https://raw.githubusercontent.com/marcopeix/MachineLearningModelDeploymentwithStreamlit/master/12_dashboard_capstone/data/quarterly_canada_population.csv"

df = pd.read_csv(URL, dtype={'Quarter': str, 
                            'Canada': np.int32,
                            'Newfoundland and Labrador': np.int32,
                            'Prince Edward Island': np.int32,
                            'Nova Scotia': np.int32,
                            'New Brunswick': np.int32,
                            'Quebec': np.int32,
                            'Ontario': np.int32,
                            'Manitoba': np.int32,
                            'Saskatchewan': np.int32,
                            'Alberta': np.int32,
                            'British Columbia': np.int32,
                            'Yukon': np.int32,
                            'Northwest Territories': np.int32,
                            'Nunavut': np.int32})

# Part 1: Title and source link
st.title("Population of Canada")
st.markdown("Source table can be found [here](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1710000901)")

# Part 2: Expandable data table
with st.expander("See full data table"):
    st.write(df)

# Part 3: Form with 3 columns
with st.form("population-form"):
    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("Choose a starting date")
        start_quarter = st.selectbox("Quarter", options=["Q1", "Q2", "Q3", "Q4"],
                                      index=2, key="start_q")
        start_year = st.slider("Year", min_value=1991, max_value=2023,
                               value=1991, step=1, key="start_y")

    with col2:
        st.write("Choose an end date")
        end_quarter = st.selectbox("Quarter", options=["Q1", "Q2", "Q3", "Q4"],
                                    index=0, key="end_q")
        end_year = st.slider("Year", min_value=1991, max_value=2023,
                             value=2023, step=1, key="end_y")

    with col3:
        st.write("Choose a location")
        target = st.selectbox("Choose a location", options=df.columns[1:], index=0)

    submit_btn = st.form_submit_button("Analyze", type="primary")

# Part 4: Combine quarter and year into date strings
start_date = f"{start_quarter} {start_year}"
end_date = f"{end_quarter} {end_year}"

# Function to convert date to number for comparison
def format_date_for_comparison(date):
    if date[1] == '2':
        return float(date[2:]) + 0.25
    elif date[1] == '3':
        return float(date[2:]) + 0.50
    elif date[1] == '4':
        return float(date[2:]) + 0.75
    else:
        return float(date[2:])

# Function to check if end date is before start date
def end_before_start(start_date, end_date):
    num_start_date = format_date_for_comparison(start_date)
    num_end_date = format_date_for_comparison(end_date)
    if num_start_date > num_end_date:
        return True
    else:
        return False
    
# Part 5: Display dashboard function
def display_dashboard(start_date, end_date, target):
    tab1, tab2 = st.tabs(["Population change", "Compare"])

    with tab1:
        st.subheader(f"Population change from {start_date} to {end_date}")

        col1, col2 = st.columns(2)

        with col1:
            # Get population values at start and end dates
            initial = df.loc[df['Quarter'] == start_date, target].item()
            final = df.loc[df['Quarter'] == end_date, target].item()

            # Calculate percentage change
            percentage_diff = round((final - initial) / initial * 100, 2)
            delta = f"{percentage_diff}%"

            # Display metrics
            st.metric(start_date, value=initial)
            st.metric(end_date, value=final, delta=delta)

        with col2:
            # Filter dataframe for date range
            start_idx = df.loc[df['Quarter'] == start_date].index.item()
            end_idx = df.loc[df['Quarter'] == end_date].index.item()
            filtered_df = df.iloc[start_idx: end_idx+1]

            # Create matplotlib chart
            fig, ax = plt.subplots()
            ax.plot(filtered_df['Quarter'], filtered_df[target])
            ax.set_xlabel('Time')
            ax.set_ylabel('Population')
            ax.set_xticks([filtered_df['Quarter'].iloc[0], filtered_df['Quarter'].iloc[-1]])
            fig.autofmt_xdate()
            st.pyplot(fig)

    with tab2:
        st.subheader('Compare with other locations')
        all_targets = st.multiselect("Choose other locations",
                                      options=filtered_df.columns[1:],
                                      default=[target])

        fig, ax = plt.subplots()
        for each in all_targets:
            ax.plot(filtered_df['Quarter'], filtered_df[each], label=each)
        ax.legend()
        ax.set_xlabel('Time')
        ax.set_ylabel('Population')
        ax.set_xticks([filtered_df['Quarter'].iloc[0], filtered_df['Quarter'].iloc[-1]])
        fig.autofmt_xdate()
        st.pyplot(fig)
    
# Part 6: Validation and display
if start_date not in df['Quarter'].tolist() or end_date not in df['Quarter'].tolist():
    st.error("No data available. Check your quarter and year selection")
elif end_before_start(start_date, end_date):
    st.error("Dates don't work. Start date must come before end date.")
else:
    display_dashboard(start_date, end_date, target)