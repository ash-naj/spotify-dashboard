import streamlit as st
from helpers import fetch_data, render_leaderboard

st.set_page_config(layout="wide")
st.write("### All-Time Top 5 Tracks")
df_tracks = fetch_data("SELECT * FROM v_top_tracks LIMIT 5;")

render_leaderboard(
    df=df_tracks,
    name_col='track',
    metric_col='total_hours',
    chart_title="Most Listened To Tracks (Hours)",
    color_theme="algae",
    is_track=True
)