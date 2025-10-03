import streamlit as st
import pandas as pd
from datetime import date
from db import (
    get_exercises,
    suggest_next_workout,
    log_workout,
    get_workouts,
    get_previous_workout,
)

st.set_page_config(page_title="Log Workout", page_icon="💪")

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

# --- Show last workout for this exercise ---
previous = get_previous_workout(exercise_name)
if previous:
    st.subheader(f"Last workout for {exercise_name}")
    st.write(
        f"📅 {previous['date']} — "
        f"{previous['sets']} sets of {previous['target_reps']} reps "
        f"at {previous['weight']}kg "
        f"(achieved: {previous['achieved_reps']}, "
        f"scheme: {previous['scheme']}, "
        f"success: {'✅' if previous['success'] else '❌'})"
    )
else:
    st.info(f"No previous workout logged for {exercise_name}.")

# --- Optional: full history in an expander ---
all_workouts = get_workouts()
if not all_workouts.empty:
    prev = all_workouts[all_workouts["Exercise"] == exercise_name]
    if not prev.empty:
        with st.expander(f"📜 Full history for {exercise_name}"):
            st.dataframe(prev, use_container_width=True)

# --- Suggest next workout ---
suggestion = suggest_next_workout(exercise_name)
st.write("### Suggested next workout")
st.json(suggestion)

# --- Input form ---
with st.form("log_workout_form"):
    workout_date = st.date_input("Workout date", value=date.today())
    weight = st.number_input(
        "Weight (kg)", min_value=0.0, step=2.5, value=float(suggestion["weight"])
    )
    sets = st.number_input(
        "Sets", min_value=1, step=1, value=int(suggestion["sets"])
    )
    target_reps = st.number_input(
        "Target reps", min_value=1, step=1, value=int(suggestion["target_reps"])
    )
    achieved_reps = st.number_input(
        "Achieved reps", min_value=0, step=1, value=int(suggestion["target_reps"])
    )
    success = st.checkbox("Success?", value=True)

    # ✅ Scheme selection (restricted options)
    scheme_options = ["3 x 15", "3 x 10", "5 x 5"]
    default_scheme = suggestion.get("scheme", "5 x 5")
    if default_scheme not in scheme_options:
        default_scheme = "5 x 5"
    scheme = st.selectbox("Scheme", scheme_options, index=scheme_options.index(default_scheme))

    # --- Buttons ---
    col1, col2 = st.columns(2)
    with col1:
        submitted = st.form_submit_button("✅ Log Workout")
    with col2:
        clear = st.form_submit_button("🗑️ Clear Form")

    if submitted:
        try:
            log_workout(
                exercise_name=exercise_name,
                weight=weight,
                sets=sets,
                target_reps=target_reps,
                achieved_reps=achieved_reps,
                success=success,
                scheme=scheme,
                workout_date=workout_date,
            )
            st.success("Workout logged!")
        except Exception as e:
            st.error(f"Error logging workout: {e}")

    if clear:
         st.rerun()