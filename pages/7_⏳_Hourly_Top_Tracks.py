import streamlit as st
import pandas as pd
from helpers import fetch_data, render_image_carousel, get_time_filter_ui

st.set_page_config(layout="wide")

start_date, end_date = get_time_filter_ui("tab7")
st.divider()
# converting to pandas
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date) + pd.Timedelta(days=1)
# getting raw data from SQL
query = "SELECT timestamp as played_at, track as track_name, artist as artist_name FROM clean_listening_history WHERE true_skip = 0;"
df_raw = fetch_data(query)
# telling pandas that timestamp is date
df_raw['timestamp'] = pd.to_datetime(df_raw['played_at'])
# getting the date from the calendar
mask = (df_raw['timestamp'] >= start_date) & (df_raw['timestamp'] < end_date)
df_filtered = df_raw[mask]
if df_filtered.empty:
    st.warning("No listening history found for this specific date range. Try expanding your search!")
else:
    # extracting the hour out of timestamp
    df_filtered['hour'] = df_filtered['timestamp'].dt.hour

    # GROUP BY & AS
    df_counts = df_filtered.groupby(['hour', 'track_name', 'artist_name']).size().reset_index(name='play_count')

    # ORDER BY & LIMIT 1
    df_top_songs = df_counts.sort_values('play_count', ascending=False).drop_duplicates(subset=['hour']).sort_values(
        'hour')

    # formatting our hour system into AM and PM
    df_top_songs['formatted_hour'] = pd.to_datetime(df_top_songs['hour'], format='%H').dt.strftime('%I %p')

    # Update the title to reflect it is dynamic now
    st.write("### Top Track by Hour")

    # the scrolling timeline
    render_image_carousel(
        df=df_top_songs,
        label_col='formatted_hour',
        primary_col='track_name',
        secondary_col='artist_name',
        is_track=True
    )