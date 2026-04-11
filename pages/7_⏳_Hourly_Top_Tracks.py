import streamlit as st
import pandas as pd
from helpers import fetch_data, render_image_carousel, render_hourly_profile, get_time_filter_ui

st.set_page_config(layout="wide")

time_filter, is_authorized = get_time_filter_ui("tab7")
if is_authorized:
    st.divider()
    # getting raw data from SQL
    query = "SELECT timestamp as played_at, track as track_name, artist as artist_name FROM clean_listening_history WHERE true_skip = 0;"
    df_raw = fetch_data(query)
    # telling pandas that timestamp is date
    df_raw['timestamp'] = pd.to_datetime(df_raw['played_at'])
    latest_date = df_raw['timestamp'].max()
    if time_filter == "Last Month":
        df_filtered = df_raw[df_raw['timestamp'] >= (latest_date - pd.DateOffset(months=1))]
    elif time_filter == "Last 2 Months":
        df_filtered = df_raw[df_raw['timestamp'] >= (latest_date - pd.DateOffset(months=2))]
    else:
        df_filtered = df_raw
    # extracting the hour out of timestamp
    df_filtered['hour'] = df_filtered['timestamp'].dt.hour
    # GROUP BY & AS
    df_counts = df_filtered.groupby(['hour', 'track_name', 'artist_name']).size().reset_index(name='play_count')
    # ORDER BY & LIMIT 1
    df_top_songs = df_counts.sort_values('play_count', ascending=False).drop_duplicates(subset=['hour']).sort_values(
        'hour')
    # formatting our hour system into AM and PM
    df_top_songs['formatted_hour'] = pd.to_datetime(df_top_songs['hour'], format='%H').dt.strftime('%I %p')
    st.write(f"### Top Track by Hour ({time_filter})")
    # the scrolling timeline
    render_image_carousel(
        df=df_top_songs,
        label_col='formatted_hour',
        primary_col='track_name',
        secondary_col='artist_name',
        is_track=True
    )