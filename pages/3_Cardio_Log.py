import streamlit as st
from datetime import date
from db import (
    log_cardio,
    get_cardio_workouts,
    get_last_cardio,
    get_cardio_exercises,
)

st.set_page_config(page_title="Cardio Log", page_icon="🏃")

st.title("🏃 Log Cardio Workout")

# --- Guard: must be signed in ---
if "user_id" not in st.session_state or not st.session_state["user_id"]:
    st.error("You must be signed in to log cardio workouts.")
    st.stop()

# --- Select cardio exercise ---
cardio_exercises = get_cardio_exercises()
if not cardio_exercises:
    st.info("No cardio exercises found. Add one first from the 'Add Cardio Exercise' page.")
    st.stop()

workout_type = st.selectbox("Workout type", cardio_exercises)

# --- Show last performance ---
last = get_last_cardio(workout_type)
if last:
    st.subheader(f"Last {workout_type} session")
    st.write(
        f"📅 {last['date']} — {last['time']} min, "
        f"{last['distance']} km, difficulty {last['difficulty']}"
    )
else:
    st.info(f"No previous {workout_type} workout logged.")

# --- Input form ---
with st.form("cardio_form"):
    workout_date = st.date_input("Workout date", value=date.today())
    time_minutes = st.number_input("Time (minutes)", min_value=1, step=1)
    distance_km = st.number_input("Distance (km)", min_value=0.0, step=0.1)
    difficulty = st.text_input("Difficulty level (e.g. 5/10, Program 3)")

    submitted = st.form_submit_button("✅ Log Cardio Workout")
    if submitted:
        try:
            log_cardio(workout_type, time_minutes, distance_km, difficulty, workout_date)
            st.success("Cardio workout logged!")
            st.rerun()
        except Exception as e:
            st.error(f"Error logging cardio workout: {e}")

# --- History ---
df = get_cardio_workouts()
if not df.empty:
    st.subheader("Your cardio history")
    st.dataframe(df, use_container_width=True)

    # Optional: filter by exercise
    exercise_filter = st.selectbox("Filter by exercise", ["All"] + sorted(df["Workout Type"].unique().tolist()))
    if exercise_filter != "All":
        df = df[df["Workout Type"] == exercise_filter]

    # Optional: chart progress
    if not df.empty:
        st.subheader("Progress over time")
        st.line_chart(df, x="Date", y="Distance (km)", color="Workout Type")
else:
    st.info("No cardio workouts logged yet.")