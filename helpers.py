import pandas as pd
import streamlit as st
import plotly.express as px
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import ssl
import datetime
import urllib.parse
import requests
import re
import time

# connecting to AIVEN
load_dotenv()
db_url = os.getenv("AIVEN_DB_URL")

# getting the data only one time, not in every function
@st.cache_resource
def get_engine():
    """Creates the database engine."""
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    return create_engine(db_url, connect_args={"ssl": ssl_context})

@st.cache_data
def fetch_data(query):
    """Getting the Data from Database and converting to pandas DataFrame."""
    return pd.read_sql(query, get_engine())

@st.cache_data
def get_artist_image(artist_name):
    import re
    import urllib.parse
    import requests
    import os

    def normalize(name):
        return name.strip().lower()

    def best_deezer_pic(artist_obj):
        """Extract the highest-res non-default picture from a Deezer artist object."""
        for size in ["picture_xl", "picture_big", "picture_medium"]:
            pic = artist_obj.get(size)
            if pic and "default" not in pic:
                return pic
        return None

    # --- METHOD 1a: Deezer — track-disambiguated search (your original idea, fixed) ---
    try:
        safe_artist = artist_name.replace("'", "''")
        query = f"""
            SELECT track 
            FROM clean_listening_history 
            WHERE artist = '{safe_artist}' AND true_skip = 0 
            GROUP BY track 
            ORDER BY COUNT(*) DESC 
            LIMIT 1;
        """
        df_top_track = fetch_data(query)

        if not df_top_track.empty:
            top_track = df_top_track.iloc[0]["track"]
            clean_track = re.sub(r'\(.*?\)', '', top_track).replace('"', '').strip()
            clean_artist = artist_name.replace('"', '').strip()

            search_query = f'track:"{clean_track}" artist:"{clean_artist}"'
            url = f"https://api.deezer.com/search?q={urllib.parse.quote(search_query)}&limit=10"
            response = requests.get(url, timeout=10)
            data = response.json()

            if data.get("data"):
                for track in data["data"]:
                    artist_obj = track.get("artist", {})
                    if normalize(artist_obj.get("name", "")) == normalize(artist_name):
                        # track result only has picture, not picture_xl — need a second call
                        artist_id = artist_obj.get("id")
                        if artist_id:
                            detail = requests.get(f"https://api.deezer.com/artist/{artist_id}", timeout=10).json()
                            pic = best_deezer_pic(detail)
                            if pic:
                                return pic

    except Exception as e:
        print(f"Deezer (track-based) Error for {artist_name}: {e}")

    # --- METHOD 1b: Deezer — direct artist search fallback ---
    try:
        url = f"https://api.deezer.com/search/artist?q={urllib.parse.quote(artist_name)}&limit=10"
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get("data"):
            # Exact match first
            for artist in data["data"]:
                if normalize(artist.get("name", "")) == normalize(artist_name):
                    pic = best_deezer_pic(artist)
                    if pic:
                        return pic
            # Best-effort: top result
            pic = best_deezer_pic(data["data"][0])
            if pic:
                return pic

    except Exception as e:
        print(f"Deezer (direct) Error for {artist_name}: {e}")

    # --- METHOD 2: TheAudioDB ---
    try:
        url = f"https://www.theaudiodb.com/api/v1/json/2/search.php?s={urllib.parse.quote(artist_name)}"
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get("artists"):
            candidates = [a for a in data["artists"] if normalize(a.get("strArtist", "")) == normalize(artist_name)]
            pool = candidates if candidates else data["artists"]  # fallback to first result if no exact match

            for artist in pool:
                for field in ["strArtistThumb", "strArtistFanart", "strArtistBanner"]:
                    img = artist.get(field)
                    if img:
                        return img + "/preview"

    except Exception as e:
        print(f"TheAudioDB Error for {artist_name}: {e}")

    # --- METHOD 3: MusicBrainz + fanart.tv ---
    try:
        mb_url = f"https://musicbrainz.org/ws/2/artist/?query=artist:{urllib.parse.quote(artist_name)}&fmt=json&limit=3"
        headers = {"User-Agent": "SpotifyAnalytics/1.0 (your@email.com)"}
        mb_data = requests.get(mb_url, headers=headers, timeout=10).json()

        if mb_data.get("artists"):
            for mb_artist in mb_data["artists"]:
                if normalize(mb_artist.get("name", "")) == normalize(artist_name):
                    mbid = mb_artist["id"]
                    ft_url = f"https://webservice.fanart.tv/v3/music/{mbid}?api_key=52a63535ea8e4fd0b3c75e7d9a0c0b69"
                    ft_data = requests.get(ft_url, timeout=10).json()

                    for key in ["artistthumb", "artistbackground", "hdmusiclogo"]:
                        images = ft_data.get(key)
                        if images:
                            return images[0]["url"]

    except Exception as e:
        print(f"MusicBrainz/fanart.tv Error for {artist_name}: {e}")

    # --- METHOD 4: Genius ---
    try:
        genius_token = os.getenv("GENIUS_ACCESS_TOKEN")

        if genius_token:
            headers = {"Authorization": f"Bearer {genius_token}"}
            response = requests.get(
                "https://api.genius.com/search",
                headers=headers,
                params={"q": artist_name},
                timeout=10
            )
            data = response.json()

            if data.get("response", {}).get("hits"):
                for hit in data["response"]["hits"]:
                    primary_artist = hit["result"]["primary_artist"]
                    if normalize(primary_artist["name"]) == normalize(artist_name):
                        img = primary_artist.get("image_url", "")
                        if img and "default_avatar" not in img:
                            return img

    except Exception as e:
        print(f"Genius Error for {artist_name}: {e}")

    # --- FINAL FALLBACK ---
    return "https://placehold.co/300x300/1a1a2e/ffffff?text=" + urllib.parse.quote(artist_name[:2].upper())

@st.cache_data
def get_track_image(track_name, artist_name):
    # Clean the text to improve search accuracy
    import re
    clean_track = re.sub(r'\(.*?\)', '', track_name).replace('"', '').strip()
    clean_artist = artist_name.replace('"', '').strip()

    # method 1, searching with deezer
    try:
        query = f'track:"{clean_track}" artist:"{clean_artist}"'
        encoded_query = urllib.parse.quote(query)
        url = f"https://api.deezer.com/search?q={encoded_query}"

        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get('data') and len(data['data']) > 0:
            tracks = data['data']

            for track in tracks:
                if track['title'].lower() == clean_track.lower():
                    # cover_medium gets the low resolution image
                    return track['album']['cover_medium']

    except Exception as e:
        print(f"Deezer Track Error for '{track_name}': {e}")

    # method 2, using itunes
    try:
        search_term = f"{clean_artist} {clean_track}"
        url = "https://itunes.apple.com/search"
        params = {
            "term": search_term,
            "entity": "song",
            "limit": 5
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get('resultCount', 0) > 0:
            tracks = data['results']

            for track in tracks:
                if track.get('trackName', '').lower() == clean_track.lower():
                    small_url = track['artworkUrl100']
                    return small_url.replace('100x100bb.jpg', '600x600bb.jpg')

            small_url = tracks[0]['artworkUrl100']
            return small_url.replace('100x100bb.jpg', '600x600bb.jpg')

    except Exception as e:
        print(f"iTunes Track Error for '{track_name}': {e}")

    # Return the default music note if the track isn't found
    return "https://cdn-icons-png.freepik.com/512/26/26805.png"

def render_leaderboard(df, name_col, metric_col, chart_title, color_theme="algae", is_track=True, chart_type="bar",
                       absolute_max=None, extra_cols=None):
    """A UI component to draw a Top 5 image leaderboard and also a data visualization."""

    # create the place for top 5 images
    top_5_df = df.head(5)
    cols = st.columns(5)

    for index, row in top_5_df.iterrows():
        # the process of getting an artist's image is different to an album cover one.
        if is_track:
            primary_name = row['track']
            artist_name = row['artist']
            image_url = get_track_image(primary_name, artist_name)
            # adds artist's name on the bottom of the image
            subtitle = f"<br><span style='font-size: 12px; color: gray;'>{artist_name}</span>"
        else:
            primary_name = row['artist']
            image_url = get_artist_image(primary_name)
            subtitle = f"<br><span style='font-size: 12px; color: gray;'>{round(row[metric_col])} plays</span>"

        with cols[index]:
            st.image(image_url, width="stretch")
            st.markdown(
                f"<p style='text-align: center; font-size: 16px;'><b>#{index + 1}</b><br>{primary_name}{subtitle}</p>",
                unsafe_allow_html=True
            )

    st.divider()

    # we create an absolute_max variable for our Table
    # if it's not provided then we set it to 100.
    chart_max = absolute_max if absolute_max is not None else df[metric_col].max()

    # creating the data visualization
    if chart_type == "table":
        display_columns = [name_col]
        if extra_cols:
            display_columns.extend(extra_cols)
        display_columns.append(metric_col)

        dynamic_label = "Track Name" if is_track else "Artist Name"
        st.dataframe(
            df[display_columns],
            column_config={
                name_col: st.column_config.TextColumn(dynamic_label),
                metric_col: st.column_config.ProgressColumn(
                    chart_title,
                    format="%.2f",
                    min_value=0,
                    max_value=chart_max,
                )
            },
            hide_index=True,
            width="stretch"
        )
    else:
        fig = px.bar(
            df, x=metric_col, y=name_col, orientation='h',
            title=chart_title, color=metric_col, color_continuous_scale=color_theme,
            text_auto='.2f',
            range_color=[0, chart_max]
        )
        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            xaxis_range=[0, chart_max],  # adds the absolute max ceiling
            # adds a padding to text
            margin=dict(l=20, r=20, t=50, b=20)
        )
        st.plotly_chart(fig, width="stretch")
# helper function for hourly charts
def render_hourly_profile(df_hourly):
    """Draws a smooth, filled, Spotify-green spline chart for hourly listening habits."""

    fig = px.line(
        df_hourly,
        x='hour',
        y='played_count',
        title="When Do I Listen to Music?",
        color_discrete_sequence=['#1DB954'],
        markers=True  # creates points on each hour
    )

    # spline does the same as smoothing, 'tozeroy' means fill under the line
    fig.update_traces(line_shape='spline', fill='tozeroy', fillcolor='rgba(29, 185, 84, 0.2)')

    fig.update_layout(
        xaxis=dict(
            tickmode='linear', tick0=0, dtick=1,  # Forces Plotly to show all 24 hours on the X axis
            title="Hour of the Day (0 = Midnight)"
        ),
        yaxis_title="Total Songs Played",
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(255, 255, 255, 0.05)',
        margin=dict(l=20, r=20, t=50, b=20)
    )

    fig.update_xaxes(showgrid=True, gridcolor='rgba(255, 255, 255, 0.1)')
    fig.update_yaxes(showgrid=True, gridcolor='rgba(255, 255, 255, 0.1)')

    st.plotly_chart(fig, width="stretch")

# helper function timeline selector
def get_time_filter_ui(tab_key):
    """A UI component for creating a calendar time selection."""
    # finding the last day of the Data and converting it to a python date object
    query = """
            SELECT MIN(DATE(timestamp)) as min_date, \
                   MAX(DATE(timestamp)) as max_date
            FROM clean_listening_history
            WHERE true_skip = 0; \
            """
    df_dates = fetch_data(query)

    # Extracting the boundaries for date
    earliest_date = pd.to_datetime(df_dates.iloc[0]['min_date']).date()
    latest_date = pd.to_datetime(df_dates.iloc[0]['max_date']).date()

    thirty_days_ago = latest_date - datetime.timedelta(days=30)
    default_start = max(thirty_days_ago, earliest_date)

    st.write("### 📅 Date Explorer")

    # all-time button that switches the timeline to all-time
    use_all_time = st.toggle("✅ Select All-Time", value=False, key=f"{tab_key}_toggle")
    if use_all_time:
        st.success("Selected Entire listening history!")
        return earliest_date, latest_date

    # two columns for start and end of the date
    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "Start Date",
            value=default_start,
            min_value=earliest_date,
            max_value=latest_date,
            key=f"{tab_key}_start"
        )

    with col2:
        end_date = st.date_input(
            "End Date",
            value=latest_date,
            min_value=earliest_date,
            max_value=latest_date,
            key=f"{tab_key}_end"
        )
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    # 4. Return them together so the rest of your app doesn't have to change!
    return start_date, end_date

def render_image_carousel(df, label_col, primary_col, secondary_col, is_track=True):
    """
    Creates a horizontally scrolling timeline of images.
    """
    html_code = "<div style='display: flex; overflow-x: auto; gap: 20px; padding-bottom: 15px; margin-bottom: 20px; scrollbar-width: thin; scrollbar-color: #1DB954 transparent;'>"
    with st.spinner('Loading images...'):
        html_code = "<div style='display: flex; overflow-x: auto; gap: 20px; padding-bottom: 15px; margin-bottom: 20px; scrollbar-width: thin; scrollbar-color: #1DB954 transparent;'>"
        for _, row in df.iterrows():
            label = str(row[label_col])

            # 1. The RAW names for the Spotify API
            raw_primary = str(row[primary_col])
            raw_secondary = str(row[secondary_col]) if secondary_col in df.columns else ""

            # 2. The SAFE names for the HTML webpage
            safe_primary = raw_primary.replace("'", "&#39;")
            safe_secondary = raw_secondary.replace("'", "&#39;")

            # 3. Fetch the image using the RAW names (Spotify needs the real apostrophe!)
            if is_track:
                image_url = get_track_image(raw_primary, raw_secondary)
            else:
                image_url = get_artist_image(raw_primary)

            # 4. Build the HTML using the SAFE names
            html_code += "<div style='flex: 0 0 140px; height: 230px; text-align: center; background-color: rgba(255,255,255,0.05); padding: 10px; border-radius: 10px; display: flex; flex-direction: column; align-items: center;'>"
            html_code += f"<div style='width: 100%; background-color: #1DB954; color: black; border-radius: 5px; padding: 3px 0px; margin-bottom: 10px; font-weight: bold; font-size: 14px;'>{label}</div>"
            html_code += f"<img src='{image_url}' style='width: 120px; height: 120px; min-width: 120px; min-height: 120px; max-width: 120px; max-height: 120px; object-fit: cover; border-radius: 5px; box-shadow: 0 4px 8px rgba(0,0,0,0.5); display: block;'>"

            # Notice we are injecting safe_primary and safe_secondary here!
            html_code += f"<div style='width: 120px; margin-top: 10px;'><p style='margin: 0px; font-size: 14px; font-weight: bold; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' title='{safe_primary}'>{safe_primary}</p></div>"
            html_code += f"<div style='width: 120px; margin-top: 2px;'><p style='margin: 0px; font-size: 12px; color: gray; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' title='{safe_secondary}'>{safe_secondary}</p></div>"
            html_code += "</div>"

        html_code += "</div>"
        st.markdown(html_code, unsafe_allow_html=True)