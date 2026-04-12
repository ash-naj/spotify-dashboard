import streamlit as st

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
        st.info(
            "🎶 **Top Tracks**\n\nA Leaderboard for most listened to Tracks.")
        st.success("🎙️ **Retained Artists**\n\nIllustrates the Artists that were played the most and were not skipped.")
        st.warning("⏰ **Hourly Plays**\n\nShows how long Music was played throughout the 24 Hours of a Day. ")
        st.error("⏳ **Hourly Top Tracks**\n\nRepresents which Track was most played throughout the Day")

    with col2:
        st.info("🎸 **Top Artists**\n\nA Leaderboard for most listened to Artists.")
        st.success("🎧 **Retained Tracks**\n\nIllustrates the Songs that were played the most and were not skipped.")
        st.warning("🗓️ **Daily Timeline**\n\nDepicts how your listening time fluctuates over weeks and months.")
        st.error("")

    st.divider()

    # A subtle footer
    st.caption("Arshia Najmaei")


if __name__ == "__main__":
    run_home_page()