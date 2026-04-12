import pandas as pd
import streamlit as st
import plotly.express as px
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import ssl
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import datetime
from dateutil.relativedelta import relativedelta

# connecting to AIVEN
load_dotenv()
db_url = os.getenv("AIVEN_DB_URL")

@st.cache_resource
def get_engine():
    """Creates the database engine ONCE and remembers it forever."""
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    return create_engine(db_url, connect_args={"ssl": ssl_context})

@st.cache_resource
def get_spotify():
    """Creates the Spotify API connection ONCE and remembers it forever."""
    return spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
        ),
        requests_timeout=10,  # Tells Spotipy to wait 10 seconds instead of 5
        retries=3
    )

# getting the data only one time, not in every function
@st.cache_data
def fetch_data(query):
    return pd.read_sql(query, get_engine())

@st.cache_data
def get_artist_image(artist_name):
    spotify = get_spotify()
    try:
        # Search Spotify for the artist
        result = spotify.search(q='artist:' + artist_name, type='artist', limit=1)
        # Dig into the data package to find the images
        images = result['artists']['items'][0]['images']
        if images:
            # If Spotify gives us at least 2 image choices, grab the Medium one [1]
            if len(images) > 1:
                return images[1]['url']
            # If they only have 1 image on file, just use whatever they gave us
            else:
                return images[0]['url']
    except Exception as e:
        pass
    return "https://img.freepik.com/premium-vector/default-avatar-profile-icon-social-media-user-image-gray-avatar-icon-blank-profile-silhouette-vector-illustration_561158-3485.jpg?w=360" # A default profile icon if there's no image

@st.cache_data
def get_track_image(track_name, artist_name):
    spotify = get_spotify()
    try:
        # Search for BOTH the track and artist to ensure we get the right song
        strict_query = f"track:{track_name} artist:{artist_name}"
        results = spotify.search(q=strict_query, type='track', limit=5)

        # Dig into the package to find the album cover images
        tracks = results['tracks']['items']

        for track in tracks:
            # Check if the name matches exactly (ignoring uppercase/lowercase)
            if track['name'].lower() == track_name.lower():
                return track['album']['images'][0]['url']
        return tracks[0]['album']['images'][0]['url']

    except Exception as e:
        print(f"Spotify API Error for '{track_name}': {e}")
        return "https://cdn-icons-png.freepik.com/512/26/26805.png"

# helper function for tabs that need a leaderboard and data visulaization
def render_leaderboard(df, name_col, metric_col, chart_title, color_theme="algae", is_track=True, chart_type="bar",
                       absolute_max=None, extra_cols=None):
    """A universal UI component to draw a Top 5 image and data visualization."""

    # create the place for top 5 images
    top_5_df = df.head(5)
    cols = st.columns(5)

    for index, row in top_5_df.iterrows():
        # the process of getting an artist's image is different to an album cover one.
        if is_track:
            primary_name = row['track']
            artist_name = row['artist']
            image_url = get_track_image(primary_name, artist_name)
            subtitle = f"<br><span style='font-size: 12px; color: gray;'>{artist_name}</span>"
        else:
            primary_name = row['artist']
            image_url = get_artist_image(primary_name)
            subtitle = ""

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

        st.dataframe(
            df[display_columns],
            column_config={
                name_col: st.column_config.TextColumn("Track Name"),
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

# helper function for the dropdown and password UI
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

    # 3. Put them side-by-side
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