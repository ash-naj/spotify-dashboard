import streamlit as st
from helpers import fetch_data, get_time_filter_ui
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
# Date selection UI
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

    st.write("### Summary")
    col1, col2, col3 = st.columns(3)

    total_days = len(df_timeline)
    avg_hours = df_timeline['hours_for_plot'].mean()

    max_day_idx = df_timeline['hours_for_plot'].idxmax()
    max_day_string = df_timeline.loc[max_day_idx, 'duration_of_session']

    max_date_raw = df_timeline.loc[max_day_idx, 'date']
    max_date_formatted = pd.to_datetime(max_date_raw).strftime('%b %d, %Y')

    avg_mins = int(avg_hours * 60)
    avg_string = f"{avg_mins // 60} hours & {avg_mins % 60} mins"

    with col1:
        st.metric("Days Tracked", f"{total_days} Days")
    with col2:
        st.metric("Daily Average", avg_string)
    with col3:
        st.metric("Most Obsessive Day", max_day_string, delta=max_date_formatted)

    st.divider()

    st.write("### Daily Listening History")

    fig = px.line(
        df_timeline,
        x='date',
        y='hours_for_plot',
        hover_data=['duration_of_session']
    )

    fig.update_traces(
        line_color='#1DB954',
        hovertemplate="<b>Date:</b> %{x}<br><b>Listened:</b> %{customdata[0]}<extra></extra>"
    )

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Hours Listened",
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor='rgba(255, 255, 255, 0.1)')

    st.plotly_chart(fig, width="stretch")