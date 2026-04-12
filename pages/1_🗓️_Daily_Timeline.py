import streamlit as st
from helpers import fetch_data, get_time_filter_ui
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# get the data using the helper function
date_range = get_time_filter_ui("tab1")

# wait till the user has selected both start and end date
if len(date_range) == 2:
    start_date, end_date = date_range
    start_date = pd.to_datetime(start_date)
    # adding 1 to include the final day as well
    end_date = pd.to_datetime(end_date) + pd.Timedelta(days=1)

    df_raw = fetch_data("SELECT * FROM v_daily_listening_summary;")
    # converting SQL to pandas
    df_raw['date'] = pd.to_datetime(df_raw['date'])
    mask = (df_raw['date'] >= start_date) & (df_raw['date'] < end_date)
    df_timeline = df_raw[mask]

    st.divider()

    if df_timeline.empty:
        st.warning("Try expanding your search!")
    else:
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
            paper_bgcolor='rgba(0, 0, 0, 0)'
        )
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=True, gridcolor='rgba(255, 255, 255, 0.1)')

        st.plotly_chart(fig, width="stretch")

else:
    # after starting to select the start date, it shows up
    st.info("👆 Please select an end date to view your timeline.")