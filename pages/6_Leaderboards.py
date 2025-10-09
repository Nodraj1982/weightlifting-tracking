import streamlit as st
from datetime import date
from db import get_pips_daily_leaderboard, get_pips_points_leaderboard

st.set_page_config(page_title="Leaderboards", page_icon="🏆")
st.title("🏆 Game Leaderboards")

# --- Guard ---
if "user_id" not in st.session_state or not st.session_state["user_id"]:
    st.error("You must be signed in to view leaderboards.")
    st.stop()

# --- Game selector ---
games = ["Pips"]  # extend later with ["Pips", "Wordle", "Connections", "Spelling Bee"]
game_choice = st.selectbox("Choose a game", games)

today = date.today()

if game_choice == "Pips":
    # --- Daily Leaderboards ---
    st.subheader(f"📅 Today's Leaderboards ({today})")
    daily = get_pips_daily_leaderboard(today)
    for diff in ["easy", "medium", "hard", "overall"]:
        st.markdown(f"**{diff.capitalize()}**")
        if diff in daily and not daily[diff].empty:
            st.dataframe(daily[diff], use_container_width=True)
        else:
            st.info(f"No scores yet for {diff}.")

    # --- Points Leaderboards ---
    st.subheader("🏆 Points Leaderboards")
    period = st.radio("Select period", ["weekly", "monthly", "all"], horizontal=True)
    points_df = get_pips_points_leaderboard(period)
    if points_df.empty:
        st.info("No points yet.")
    else:
        st.dataframe(points_df, use_container_width=True)

else:
    st.info(f"Leaderboards for {game_choice} are not implemented yet.")