import streamlit as st
import pandas as pd
from helpers import fetch_data, get_time_filter_ui, render_hourly_profile

st.set_page_config(layout="wide")

# Grab the dates from your new two-box calendar
start_date, end_date = get_time_filter_ui("tab6")

st.divider()

# convert to pandas
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date) + pd.Timedelta(days=1)

# grabbing the raw data
query = "SELECT timestamp FROM clean_listening_history WHERE true_skip = 0;"
df_raw = fetch_data(query)

df_raw['timestamp'] = pd.to_datetime(df_raw['timestamp'])

# use the data from the calendar
mask = (df_raw['timestamp'] >= start_date) & (df_raw['timestamp'] < end_date)
df_filtered = df_raw[mask]
if df_filtered.empty:
    st.warning("No listening history found for this specific date range. Try expanding your search!")
else:
    df_filtered = df_filtered.copy()
    df_filtered['hour'] = df_filtered['timestamp'].dt.hour
    # GROUP BY
    df_hourly = df_filtered.groupby('hour').size().reset_index(name='played_count')

    # Create a perfect 24-hour timeline
    all_hours = pd.DataFrame({'hour': range(24)})
    df_hourly = pd.merge(all_hours, df_hourly, on='hour', how='left').fillna(0)

    df_hourly['played_count'] = df_hourly['played_count'].astype(int)

    st.write("### Hourly Listening Profile")

    render_hourly_profile(df_hourly)