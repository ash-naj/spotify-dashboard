import streamlit as st
from helpers import fetch_data, get_time_filter_ui, render_hourly_profile

time_filter, is_authorized = get_time_filter_ui("tab6")
if is_authorized:
    st.divider()
    df_master = fetch_data("SELECT * FROM v_hourly_plays;")
    if time_filter == "Last Month":
        target_column = 'last_30_days_plays'
    elif time_filter == "Last 2 Months":
        target_column = 'last_60_days_plays'
    else:
        target_column = 'all_time_plays'
    df_hourly = df_master[['hour', target_column]].rename(columns={target_column: 'played_count'})
    render_hourly_profile(df_hourly)