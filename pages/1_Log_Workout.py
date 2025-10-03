import streamlit as st
import pandas as pd
from datetime import date
from db import get_exercises, suggest_next_workout, log_workout, get_workouts

st.set_page_config(page_title="Log Workout", page_icon="💪")

st.write("Current user_id:", st.session_state.get("user_id"))

st.title("💪 Log a Workout")

# --- Guard: must be signed in ---
if "user_id" not in st.session_state or not st.session_state["user_id"]:
    st.error("You must be signed in to log a workout.")
    st.stop()

# --- Select exercise ---
exercises = get_exercises()
if not exercises:
    st.info("No exercises found. Add one first from the 'Add Exercise' page.")
    st.stop()

exercise_name = st.selectbox("Choose an exercise", exercises)

# --- Show previous workouts for this exercise ---
all_workouts = get_workouts()
if not all_workouts.empty:
    prev = all_workouts[all_workouts["Exercise"] == exercise_name]
    if not prev.empty:
        st.subheader(f"Previous workouts for {exercise_name}")
        st.dataframe(prev, use_container_width=True)
    else:
        st.info(f"No previous workouts logged for {exercise_name}.")
else:
    st.info("No workouts logged yet.")

# --- Suggest next workout ---
suggestion = suggest_next_workout(exercise_name)
st.write("### Suggested next workout")
st.json(suggestion)

# --- Input form ---
with st.form("log_workout_form"):
    workout_date = st.date_input("Workout date", value=date.today())
    weight = st.number_input("Weight (kg)", min_value=0.0, step=2.5, value=float(suggestion["weight"]))
    sets = st.number_input("Sets", min_value=1, step=1, value=int(suggestion["sets"]))
    target_reps = st.number_input("Target reps", min_value=1, step=1, value=int(suggestion["target_reps"]))
    achieved_reps = st.number_input("Achieved reps", min_value=0, step=1, value=int(suggestion["target_reps"]))
    success = st.checkbox("Success?", value=True)
    scheme = st.text_input("Scheme", value=suggestion["scheme"])

    submitted = st.form_submit_button("Log Workout")

    if submitted:
        try:
            # Pass workout_date into your DB insert
            log_workout(
                exercise_name=exercise_name,
                weight=weight,
                sets=sets,
                target_reps=target_reps,
                achieved_reps=achieved_reps,
                success=success,
                scheme=scheme,
                # You’ll need to update db.log_workout to accept workout_date
                workout_date=workout_date,
            )
        except Exception as e:
            st.error(f"Error logging workout: {e}")