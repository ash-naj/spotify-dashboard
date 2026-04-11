import streamlit as st
from helpers import fetch_data, render_leaderboard

st.set_page_config(layout="wide")
st.write("### All-Time Top 10 Retained Artists")
with st.expander("🤓 How is this calculated? (The Math)"):
    st.write("""
    I'm using LOG to normalize the play count, to avoid having tracks with high play counts at the top of the list.
    \nAlbeit, LOG has no natural ceiling, so to get a clean percentage we use the (Max total play(most played tracks)) in the dataset as the divisor.
    \nresult is a 0–100 score: higher = listened to often AND rarely skipped
    """)
df_retained = fetch_data("SELECT * FROM v_weighted_artist_skip_percentage LIMIT 10;")
render_leaderboard(
    df=df_retained,
    name_col='artist',
    metric_col='weighted_skip_percentage',
    chart_title="Retention Score",
    color_theme="Teal",
    is_track=False,
    chart_type="table",
    absolute_max=100,
    extra_cols=['total_plays', 'total_skips']
)
st.divider()