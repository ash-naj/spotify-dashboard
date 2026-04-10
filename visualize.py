import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline
import streamlit as st
import plotly.express as px
from sqlalchemy import create_engine
from sqlalchemy import text
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

# visualization for 4__Total_Plays_per_Hour.csv
def hourly_graph():
    query = "SELECT * FROM clean_listening_history"
    df = pd.read_sql(query, engine)

    # creates 300 x points, between 0 and 23
    x_smooth = np.linspace(df['hour'].min(), df['hour'].max(), 300)
    # k is the degree of the polynomial of the new, smooth, graph
    spline = make_interp_spline(df['hour'], df['played_count'], k=3)
    # spline is an object that gets the x value and outputs the y value, using 'make_interp_spline'
    y_smooth = spline(x_smooth)

    # creates the canvas for the plot, because we have 24 x indexes, we use 12 and 6.
    plt.figure(figsize=(12,6))
    # marker indicates that we need dots on the graph, not a smooth continuous line
    plt.plot(x_smooth, y_smooth, marker='o', color='#861891', linewidth=2.5)
    # during the smoothing process, therefor numbers can be generated with negative values, 'np.maximum' gets rid of those
    plt.fill_between(x_smooth, np.maximum(y_smooth, 0), color='#861891', alpha=0.2)
    # this is the original graph, no smoothing
    plt.plot(df['hour'], df['played_count'], marker='o', color='#1DB954', linestyle='none')
    plt.title('Total Spotify Plays by Hour of the Day', fontsize=16, fontweight='bold')
    plt.xlabel('Hour of the Day (0 = Midnight)', fontsize=12)
    plt.ylabel('Total Songs Played', fontsize=12)
    # matplotlib would automatically compress the x values, this avoids it
    plt.xticks(range(0, 24))
    # creates the grid in the background
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    # squishes the graph inward so every label fits inside the graph
    plt.tight_layout()
    plt.savefig('Graphs/4__Total_Plays_per_Hour.png', dpi=600)
    plt.show()

# visualization for 7__Days_with_Longest_Music_Sessions.csv
def daily_session_duration():
    query = """
            SELECT DATE(timestamp)                   AS date, \
                   SUM(ms_duration) / (1000 * 60 * 60) AS hours_for_plot
            FROM clean_listening_history
            GROUP BY DATE(timestamp)
            ORDER BY date; \
            """
    df = pd.read_sql(query, engine)
    df['date'] = pd.to_datetime(df['date'])
    plt.figure(figsize=(14, 6))
    plt.plot(df['date'], df['hours_for_plot'], color='#75FAED', linewidth=2)
    plt.title('Daily Spotify Listening Timeline')
    # gcf --> get current figure
    # the second part enhances the way matplotlib shows dates on the plot
    plt.gcf().autofmt_xdate()
    plt.tight_layout()
    plt.savefig('Graphs/7__Days_with_Longest_Music_Sessions.png', dpi=600)
    plt.show()

def daily_session_duration_streamlit():
    st.title("My Spotify Wrapped Dashboard 🎧")

    # creating different tabs
    tab1, tab2, tab3 = st.tabs(["🗓️ Daily Timeline", "🎸 Top Artists", "🎶 Top Tracks"])
    # tab1 : listening history graph
    with tab1:
        # Creating two columns for our controls
        col1, col2 = st.columns(2)
        with col1:
            st.write("### Filter Your History")
            time_filter = st.selectbox(
                "Select Time Window:",
                ["Last Month", "Last 2 Months", "All Time (Restricted)"]
            )

            if time_filter == "Last Month":
                query = """
                        SELECT * FROM v_daily_listening_summary
                        WHERE date >= (SELECT MAX(date) FROM v_daily_listening_summary) - INTERVAL 30 DAY;
                        """
            elif time_filter == "Last 2 Months":
                query = """
                        SELECT * \
                        FROM v_daily_listening_summary
                        WHERE date >= (SELECT MAX(date) FROM v_daily_listening_summary) - INTERVAL 2 MONTH; \
                        """
            # all time data access
            else:
                with col2:
                    st.write("### Welcome Mr.Stark")
                    secret_pass = st.text_input("Enter password", type="password")
                if secret_pass == "AbBaba":
                    st.success("Welcome Mr.Stark! Fetching all the data for you sir...")
                    query = "SELECT * FROM v_daily_listening_summary;"
                else:
                    st.warning("⚠️ Jarvis won't allow you")
                    return

        df_timeline = fetch_data(query)
        df_timeline['date'] = pd.to_datetime(df_timeline['date'])
        # UI
        st.divider()
        st.write("### Graph Smoothing")
        # smoother slide dynamically changes based on the selected time window
        if time_filter in ["Last Month", "Last 2 Months"]:
            max_slider_val = 7
            slider_label = "1 = Raw Data, 7 = Weekly Trend"
        else:
            max_slider_val = 30
            slider_label = "1 = Raw Data, 30 = Monthly Trend"

        smoothness = st.slider(
            slider_label,
            min_value=1,
            max_value=max_slider_val,
            value=1
        )
        if smoothness == 1:
            df_timeline['plot_value'] = df_timeline['hours_for_plot']
            chart_title = f'Raw Data, Daily Listening Timeline ({time_filter})'
        else:
            df_timeline['plot_value'] = df_timeline['hours_for_plot'].rolling(window=smoothness, min_periods=1).mean()
            chart_title = f'{smoothness}-Day Average, Daily Listening Timeline ({time_filter})'
        fig1 = px.line(df_timeline,
                       x='date',
                       y='plot_value',
                       title=chart_title,
                       custom_data=['hours_for_plot'],
                       color_discrete_sequence=['#1DB954'])
        fig1.update_layout(yaxis_title="Hours Listened")
        # adds vertical time grids
        fig1.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(255, 255, 255, 0.1)',  # creates a faint white line for every x months
            # the number indicates the distance between ticks
            dtick="M3",

            # Format the text at the bottom to say "Jan 2024" instead of raw dates
            tickformat="%b %Y"
        )
        # it changes the data that it will be shown when the mouse is hovering on the graph
        if smoothness == 1:
            fig1.update_traces(
                # got no idea how this works, used AI
                hovertemplate="<b>Date:</b> %{x|%B %d, %Y}<br>" +
                              "<b>Hours Listened:</b> %{customdata[0]:.2f}<br>"
            )
        else :
            fig1.update_traces(
                hovertemplate="<b>Date:</b> %{x|%B %d, %Y}<br>" +
                              "<b>Actual Hours Listened:</b> %{customdata[0]:.2f}<br>" +
                              "<b>Smoothed Trend:</b> %{y:.2f}<extra></extra>"
            )
        # adds the slider
        fig1.update_layout(xaxis=dict(rangeslider=dict(visible=False)))
        st.plotly_chart(fig1, use_container_width=True)
    # tab2 : top 5 artists
    with tab2:
        st.write("### All-Time Top 5 Artists")
        # get the data from the created Table
        top_artists_query = "SELECT * FROM v_top_artists LIMIT 5;"
        df_artists = fetch_data(top_artists_query)
        # columns for artist picture
        cols = st.columns(5)
        # goes through the 5 artist and gets their images
        for index, row in df_artists.iterrows():
            image_url = get_artist_image(row['artist'])
            with cols[index]:
                st.image(image_url, use_container_width=True)
                # Adds the artist name in bold below their picture
                st.markdown(
                    f"<p style='text-align: center; font-size: 18px;'><b>#{index + 1}</b><br>{row['artist']}</p>",
                    unsafe_allow_html=True)
        # creating a bar chart
        fig2 = px.bar(
            df_artists,
            x='total_hours',
            y='artist',
            orientation='h',
            title="Most Listened To Artists",
            color='total_hours',
            color_continuous_scale="Purp"
        )
        # reversing the Y-axis
        fig2.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig2, use_container_width=True)
    with tab3:
        st.write("### All-Time Top 5 Tracks")
        top_tracks_query = "SELECT * FROM v_top_tracks LIMIT 5;"
        df_tracks = fetch_data(top_tracks_query)
        # getting track pictures
        cols_tracks = st.columns(5)
        for index, row in df_tracks.iterrows():
            track_name = row['track']
            artist_name = row['artist']
            image_url = get_track_image(track_name, artist_name)

            with cols_tracks[index]:
                st.image(image_url, use_container_width=True)
                # Adds Rank, Track Name (bold), and Artist Name (smaller and gray)
                st.markdown(
                    f"<p style='text-align: center; font-size: 16px;'><b>#{index + 1}</b><br>{track_name}<br><span style='font-size: 12px; color: gray;'>{artist_name}</span></p>",
                    unsafe_allow_html=True
                )

        st.divider()
        # creating a bar chart
        fig3 = px.bar(
            df_tracks,
            x='total_hours',
            y='track',
            orientation='h',
            title="Most Listened To Tracks",
            color='total_hours',
            color_continuous_scale="Purp"
        )
        # reversing the Y-axis
        fig3.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig3, use_container_width=True)
# run this file in terminal
if __name__ == "__main__":
    daily_session_duration_streamlit()