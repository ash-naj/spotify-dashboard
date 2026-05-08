import streamlit as st
from streamlit import switch_page

st.set_page_config(layout="wide")
def run_home_page():
    # 'centered' layout often looks much sleeker for a pure landing page!
    st.set_page_config(
        page_title="Spotify Wrapped Dashboard",
        page_icon="🎧",
    )

    st.title("🎧 Spotify Wrapped")
    st.markdown("*Spotify Wrapped But On Steroids.*")
    st.divider()

    st.write(
        "Use the sidebar menu to navigate between modules to see what they do:")
    st.write("") # adds a blank space (baby And I'll write your name)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        with st.container(border=True):
            st.info("🎶 **Top Tracks**\n\nA Leaderboard for most listened to Tracks.")
            if st.button("View Top Tracks", use_container_width=True):
                st.switch_page('pages/3_🎶_Top_Tracks.py')

        with st.container(border=True):
            st.success("🎙️ **Retained Artists**\n\nIllustrates the Artists that were played the most and were not skipped.")
            if st.button("View Retained Artists", use_container_width=True):
                st.switch_page('pages/5_🎙️_Retained_Artists.py')

        with st.container(border=True):
            st.warning("⏰ **Hourly Plays**\n\nShows how long Music was played throughout the 24 Hours of a Day. ")
            if st.button("View Hourly Plays", use_container_width=True):
                st.switch_page('pages/6_⏰_Hourly_Plays.py')

        with st.container(border=True):
            st.error("⏳ **Hourly Top Tracks**\n\nRepresents which Track was most played throughout the Day.")
            if st.button("View Hourly Top Tracks", use_container_width=True):
                st.switch_page('pages/7_⏳_Hourly_Top_Tracks.py')
    with col2:
        with st.container(border=True):
            st.info("🎸 **Top Artists**\n\nA Leaderboard for most listened to Artists.")
            if st.button("View Top Artists", use_container_width=True):
                st.switch_page('2_🎸_Top_Artists.py')

        with st.container(border=True):
            st.success("🎧 **Retained Tracks**\n\nIllustrates the Songs that were played the most and were not skipped.")
            if st.button("View Retained Tracks", use_container_width=True):
                switch_page('pages/4_🎧_Retained_Tracks.py')

        with st.container(border=True):
            st.warning("🗓️ **Daily Timeline**\n\nDepicts how listening sessions fluctuated throughout Time.")
            if st.button("View Daily Timeline", use_container_width=True):
                switch_page('pages/1_🗓️_Daily_Timeline.py')

        with st.container(border=True):
            st.error("🕰️ **Periodic Leaderboard**\n\nCreates a Custom Leaderboard for the Selected Time Period.")
            if st.button("View Periodic Leaderboard", use_container_width=True):
                switch_page('pages/8_🕰️_Periodic_Leaderboard.py')

    st.divider()

    # A subtle footer
    st.caption("Arshia Najmaei")


if __name__ == "__main__":
    run_home_page()