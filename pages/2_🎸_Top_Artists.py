import streamlit as st
from helpers import fetch_data, render_leaderboard

st.set_page_config(layout="wide")
st.write("### All-Time Top 5 Artists")
df_artists = fetch_data("SELECT * FROM v_top_artists LIMIT 5;")

render_leaderboard(
    df=df_artists,
    name_col='artist',
    metric_col='total_hours',
    chart_title="Most Listened To Artists (Hours)",
    color_theme="algae",
    is_track=False # tells the helper function that we need artist images
)