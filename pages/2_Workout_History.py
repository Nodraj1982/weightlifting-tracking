import streamlit as st
from db import get_workouts

st.set_page_config(page_title="Workout History", page_icon="📜")

st.title("📜 Workout History")

# --- Guard: must be signed in ---
if "user_id" not in st.session_state or not st.session_state["user_id"]:
    st.error("You must be signed in to view your workout history.")
    st.stop()

# --- Fetch workouts ---
df = get_workouts()

if df.empty:
    st.info("No workouts logged yet. Head to 'Log Workout' to add your first one!")
    st.stop()

# --- Display table ---
st.subheader("Your logged workouts")
st.dataframe(df, use_container_width=True)

# --- Optional: filter by exercise ---
exercise_filter = st.selectbox("Filter by exercise", ["All"] + sorted(df["Exercise"].unique().tolist()))
if exercise_filter != "All":
    df = df[df["Exercise"] == exercise_filter]

# --- Optional: chart progress ---
st.subheader("Progress over time")
if not df.empty:
    chart_data = df[["Date", "Weight", "Exercise"]]
    st.line_chart(chart_data, x="Date", y="Weight", color="Exercise")
else:
    st.info("No data available for the selected filter.")