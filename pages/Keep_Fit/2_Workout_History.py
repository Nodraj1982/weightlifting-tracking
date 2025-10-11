import streamlit as st
from db import get_workouts, get_cardio_workouts

st.set_page_config(page_title="Workout History", page_icon="📜")

st.title("📜 Workout History")

# --- Guard: must be signed in ---
if "user_id" not in st.session_state or not st.session_state["user_id"]:
    st.error("You must be signed in to view your workout history.")
    st.stop()

# --- Initial filter: Strength or Cardio ---
history_type = st.radio(
    "Choose which history to view:",
    ["Strength", "Cardio"],
    index=None,  # forces user to pick before anything loads
    horizontal=True
)

if history_type is None:
    st.info("Please select Strength or Cardio to view your history.")
    st.stop()

# --- Strength history ---
if history_type == "Strength":
    df = get_workouts()
    if df.empty:
        st.info("No strength workouts logged yet. Head to 'Log Workout' to add your first one!")
        st.stop()

    st.subheader("Your Strength Workouts")
    st.dataframe(df, use_container_width=True)

    # Optional: filter by exercise
    exercise_filter = st.selectbox("Filter by exercise", ["All"] + sorted(df["Exercise"].unique().tolist()))
    if exercise_filter != "All":
        df = df[df["Exercise"] == exercise_filter]

    st.dataframe(df, use_container_width=True)

# --- Cardio history ---
elif history_type == "Cardio":
    df = get_cardio_workouts()
    if df.empty:
        st.info("No cardio workouts logged yet. Head to 'Log Cardio Workout' to add your first one!")
        st.stop()

    st.subheader("Your Cardio Workouts")
    st.dataframe(df, use_container_width=True)

    # Optional: filter by activity
    activity_filter = st.selectbox("Filter by activity", ["All"] + sorted(df["Workout Type"].unique().tolist()))
    if activity_filter != "All":
        df = df[df["Workout Type"] == activity_filter]

    st.dataframe(df, use_container_width=True)