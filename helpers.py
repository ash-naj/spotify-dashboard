import pandas as pd
import streamlit as st
import plotly.express as px
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import ssl
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# connecting to AIVEN
load_dotenv()
db_url = os.getenv("AIVEN_DB_URL")
# spotify API connection
spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
))

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

engine = create_engine(
    db_url,
    connect_args={
        "ssl": ssl_context
    }
)

# getting the data only one time, not in every function
@st.cache_data
def fetch_data(query):
    return pd.read_sql(query, engine)

@st.cache_data
def get_artist_image(artist_name):
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
    try:
        # Search for BOTH the track and artist to ensure we get the right song
        query = f"track:{track_name} artist:{artist_name}"
        result = spotify.search(q=query, type='track', limit=1)

        # Dig into the package to find the album cover images
        images = result['tracks']['items'][0]['album']['images']

        if images:
            # The exact same quality check we used for artists!
            if len(images) > 1:
                return images[1]['url']  # Grab the medium resolution
            else:
                return images[0]['url']

    except Exception as e:
        pass

    return "https://via.placeholder.com/300?text=No+Cover"

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
            st.image(image_url, use_container_width=True)
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
            use_container_width=True
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
        st.plotly_chart(fig, use_container_width=True)
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

    st.plotly_chart(fig, use_container_width=True)

# helper function for the dropdown and password UI
def get_time_filter_ui(tab_key):
    """A UI component for selecting time windows and passwords."""
    col1, col2 = st.columns(2)
    with col1:
        st.write("### Filter Your History")
        time_filter = st.selectbox(
            "Select Time Window:",
            ["Last Month", "Last 2 Months", "All Time (Restricted)"],
            key=f"time_filter_{tab_key}" # creating a different key based off of the tab name
        )

    if time_filter == "All Time (Restricted)":
        with col2:
            st.write("### Welcome Mr.Stark")
            secret_pass = st.text_input("Enter password", type="password", key=f"password_{tab_key}")
        if secret_pass == "AbBaba":
            st.success("Welcome Mr.Stark! Fetching all the data for you sir...")
            return time_filter, True
        else:
            st.warning("⚠️ Jarvis won't allow you")
            return time_filter, False
    return time_filter, True