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

load_dotenv()
db_url = os.getenv("AIVEN_DB_URL")
engine = create_engine(db_url, connect_args={"ssl": {"ssl_disabled": True}})

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
                   SUM(ms_played) / (1000 * 60 * 60) AS hours_for_plot
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
    query = """
            SELECT DATE(timestamp)                   AS date,
                   SUM(ms_played) / (1000 * 60 * 60) AS hours_for_plot
            FROM clean_listening_history
            GROUP BY DATE(timestamp)
            ORDER BY date; \
            """
    df = pd.read_sql(query, engine)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by=['date'])
    # UI
    st.write("### Slider for Graph Smoothing")
    smoothness = st.slider (
        "Slider : 1 --> Raw Data, 30 --> Monthly Trend ",
        min_value = 1,
        max_value = 30,
        value = 1
    )
    if smoothness == 1:
        df['plot_value'] = df['hours_for_plot']
        chart_title = 'Raw Data, Daily Listening Timeline'
    else:
        df['plot_value'] = df['hours_for_plot'].rolling(window=smoothness).mean()
        chart_title = f'{smoothness}-Day Average, Daily Listening Timeline'
    fig = px.line(df, x='date', y='plot_value', title=chart_title, custom_data=['hours_for_plot'])
    # adds vertical time grids
    fig.update_xaxes(
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
        fig.update_traces(
            # got no idea how this works, used AI
            hovertemplate="<b>Date:</b> %{x|%B %d, %Y}<br>" +
                          "<b>Hours Listened:</b> %{customdata[0]:.2f}<br>"
        )
    else :
        fig.update_traces(
            hovertemplate="<b>Date:</b> %{x|%B %d, %Y}<br>" +
                          "<b>Actual Hours Listened:</b> %{customdata[0]:.2f}<br>" +
                          "<b>Smoothed Trend:</b> %{y:.2f}<extra></extra>"
        )
    # adds the slider
    fig.update_layout(xaxis=dict(rangeslider=dict(visible=True)))
    st.plotly_chart(fig, use_container_width=True)

# run this file in terminal
daily_session_duration_streamlit()