import streamlit as st
from datetime import date
from db import log_pips_score, log_nyt_score, get_pips_daily_leaderboard, get_pips_points_leaderboard

st.set_page_config(page_title="Log Scores", page_icon="📝")
st.title("📝 Log NYT Game Scores & Leaderboards")

# --- Guard ---
if "user_id" not in st.session_state or not st.session_state["user_id"]:
    st.error("You must be signed in to log scores.")
    st.stop()

today = date.today()

# --- Choose game ---
games = ["Pips", "Wordle", "Connections", "Spelling Bee"]
game_choice = st.selectbox("Choose a game", games)

# --- Input form ---
with st.form("pips_scores_form"):
    st.subheader(f"Log your scores for {today}")

    st.markdown("**Easy**")
    easy_min = st.number_input("Minutes (Easy)", min_value=0, step=1, key="easy_min")
    easy_sec = st.number_input("Seconds (Easy)", min_value=0, max_value=59, step=1, key="easy_sec")

    st.markdown("**Medium**")
    medium_min = st.number_input("Minutes (Medium)", min_value=0, step=1, key="medium_min")
    medium_sec = st.number_input("Seconds (Medium)", min_value=0, max_value=59, step=1, key="medium_sec")

    st.markdown("**Hard**")
    hard_min = st.number_input("Minutes (Hard)", min_value=0, step=1, key="hard_min")
    hard_sec = st.number_input("Seconds (Hard)", min_value=0, max_value=59, step=1, key="hard_sec")

    submitted = st.form_submit_button("✅ Submit Scores")

    if submitted:
        try:
            if easy_min or easy_sec:
                log_pips_score("easy", easy_min * 60 + easy_sec, today)
            if medium_min or medium_sec:
                log_pips_score("medium", medium_min * 60 + medium_sec, today)
            if hard_min or hard_sec:
                log_pips_score("hard", hard_min * 60 + hard_sec, today)
            st.success("Scores logged!")
            st.rerun()
        except Exception as e:
            st.error(f"Error logging scores: {e}")

# --- Leaderboards ---
if game_choice == "Pips":
    st.subheader("📅 Today's Leaderboards")
    daily = get_pips_daily_leaderboard(today)
    for diff in ["easy", "medium", "hard", "overall"]:
        st.markdown(f"**{diff.capitalize()}**")
        if diff in daily and not daily[diff].empty:
            st.dataframe(daily[diff], use_container_width=True)
        else:
            st.info(f"No scores yet for {diff}.")

    st.subheader("🏆 Points Leaderboards")
    period = st.radio("Select period", ["weekly", "monthly", "all"], horizontal=True)
    points_df = get_pips_points_leaderboard(period)
    if points_df.empty:
        st.info("No points yet.")
    else:
        st.dataframe(points_df, use_container_width=True)
else:
    st.info(f"Leaderboards for {game_choice} not implemented yet.")