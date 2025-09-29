import streamlit as st
from utils import ensure_session_keys
from db import get_exercises, log_workout

st.header("Log Workout")
ensure_session_keys()

if st.session_state.get("user_id"):
    exercise_names = get_exercises()
    if exercise_names:
        exercise = st.selectbox("Exercise", exercise_names)
        weight = st.number_input("Weight (kg)", min_value=0, step=1)
        target_reps = st.number_input("Target Reps", min_value=1, step=1)
        achieved_reps = st.number_input("Achieved Reps", min_value=0, step=1)
        success = st.checkbox("Success (hit target reps?)")

        if st.button("Save Workout"):
            log_workout(
                exercise,
                weight,
                target_reps,
                achieved_reps,
                success,
                st.session_state.user_id
            )
    else:
        st.info("No exercises found. Seed the exercises table first.")
else:
    st.warning("Please log in on the Home page first.")