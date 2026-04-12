import streamlit as st
import pandas as pd
from helpers import fetch_data, get_time_filter_ui, get_artist_image, get_track_image

st.set_page_config(layout="wide")

start_date, end_date = get_time_filter_ui("tab8")
st.divider()

# converting start and end dates to pandas date
start_date , end_date = pd.to_datetime(start_date), pd.to_datetime(end_date)
# getting the raw data form SQL
query = ("SELECT timestamp, track as track_name, artist as artist_name FROM clean_listening_history WHERE true_skip = 0;")
df_raw = fetch_data(query)
# converting dates to pandas date
df_raw['timestamp'] = pd.to_datetime(df_raw['timestamp'])

mask = (df_raw['timestamp'] >= start_date) & (df_raw['timestamp'] < end_date)
df_filtered = df_raw[mask]

if df_filtered.empty:
    st.warning("No listening history for this time range")
else :
    col1, col2 = st.columns(2)
    with col1:
        mode = st.radio("What are we ranking?", ["Artists", "Tracks"], horizontal=True)
    with col2:
        period = st.radio("Time Period", ["Weekly", "Monthly", "Yearly"], horizontal=True)

    # a dictionary for pandas
    freq_map = {"Weekly": "W", "Monthly": "M", "Yearly": "Y"}
    freq_code = freq_map[period]

    df_filtered = df_filtered.copy()
    # filtering based off of period
    df_filtered['period'] = df_filtered['timestamp'].dt.to_period(freq_code)

    target_col = 'artist_name' if mode == "Artists" else 'track_name'
    group_cols = ['period', target_col]
    if mode == "Tracks":
        group_cols.append('artist_name')  # Need artist for track images

    # GROUP BY timestamp / period
    df_counts = df_filtered.groupby(group_cols).size().reset_index(name='plays')
    # ORDER BY period
    df_winners = df_counts.sort_values(['period', 'plays'], ascending=[True, False]).drop_duplicates(subset=['period'])

    # converting periods into readable text
    if period == "Monthly":
        df_winners['display_date'] = df_winners['period'].dt.strftime('%b %Y')
    elif period == "Yearly":
        df_winners['display_date'] = df_winners['period'].dt.strftime('%Y')
    else:  # Weekly
        df_winners['display_date'] = df_winners['period'].dt.start_time.dt.strftime('%b %d %Y') + " ~~ " + df_winners['period'].dt.end_time.dt.strftime('%b %d %Y')

    st.write(f"### Your Top {mode} Over Time")

    grid_html = "<div style='display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 24px; padding-top: 20px;'>"

    # adds a loading message
    with st.spinner(f"Loading {len(df_winners)} covers..."):
        for _, row in df_winners.iterrows():
            date_label = row['display_date']
            plays = row['plays']

            if mode == "Artists":
                name = row['artist_name']
                image_url = get_artist_image(name)
                subtitle = "Artist"
                # crop artist images into circles, to look like spotify's ranking page
                img_style = "border-radius: 50%; aspect-ratio: 1 / 1; object-fit: cover; width: 100%; box-shadow: 0 8px 16px rgba(0,0,0,0.5);"
            else:
                name = row['track_name']
                artist = row['artist_name']
                image_url = get_track_image(name, artist)
                subtitle = artist
                # Album covers get slightly rounded square edges
                img_style = "border-radius: 8px; aspect-ratio: 1 / 1; object-fit: cover; width: 100%; box-shadow: 0 8px 16px rgba(0,0,0,0.5);"

            safe_name = str(name).replace("'", "&#39;")
            safe_subtitle = str(subtitle).replace("'", "&#39;")

            # AI Code
            grid_html += f"<div style='display: flex; flex-direction: column; align-items: center; background-color: rgba(255,255,255,0.03); padding: 15px; border-radius: 12px; transition: background-color 0.3s;'>"
            grid_html += f"<div style='width: 100%; margin-bottom: 12px;'>"
            grid_html += f"<img src='{image_url}' style='{img_style}'>"
            grid_html += f"</div>"
            grid_html += f"<div style='text-align: left; width: 100%;'>"
            grid_html += f"<p style='margin: 0; font-size: 15px; font-weight: bold; color: white; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' title='{safe_name}'>{safe_name}</p>"
            grid_html += f"<p style='margin: 0; font-size: 13px; color: #b3b3b3; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'>{safe_subtitle}</p>"
            grid_html += f"<p style='margin: 6px 0 0 0; font-size: 12px; font-weight: bold; color: #1DB954;'>{date_label} &bull; {plays} plays</p>"
            grid_html += f"</div>"
            grid_html += f"</div>"

    grid_html += "</div>"
    st.markdown(grid_html, unsafe_allow_html=True)