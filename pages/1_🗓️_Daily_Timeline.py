import streamlit as st
from helpers import fetch_data, get_time_filter_ui
import pandas as pd
import plotly.express as px

# Creating two columns for our controls
time_filter, is_authorized = get_time_filter_ui("tab1")
if is_authorized:
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
    else:
        query = "SELECT * FROM v_daily_listening_summary;"
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