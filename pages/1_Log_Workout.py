import streamlit as st
from utils import ensure_session_keys
from db import get_exercises, log_workout, suggest_next_workout

st.header("Log Workout")
ensure_session_keys()

if st.session_state.get("user_id"):
    exercise_names = get_exercises()
    if exercise_names:
        exercise = st.selectbox("Exercise", exercise_names)

        # Automatically fetch suggestion when exercise is chosen
        if exercise:
            suggestion = suggest_next_workout(st.session_state.user_id, exercise)
            st.session_state.suggested = suggestion
            st.info(
                f"Suggested: {suggestion['scheme']} at {suggestion['weight']} kg "
                f"({suggestion['target_reps']} reps)"
            )

        # Pre-fill inputs with suggestion
        suggested = st.session_state.get("suggested", {})
        weight = st.number_input(
            "Weight (kg)", min_value=0, step=1, value=suggested.get("weight", 0)
        )
        target_reps = st.number_input(
            "Target Reps", min_value=1, step=1, value=suggested.get("target_reps", 10)
        )
        achieved_reps = st.number_input("Achieved Reps", min_value=0, step=1)
        success = st.checkbox("Success (hit target reps?)")
        scheme = suggested.get("scheme", f"3x{target_reps}")

        if st.button("Save Workout"):
            log_workout(
                exercise,
                weight,
                target_reps,
                achieved_reps,
                success,
                st.session_state.user_id,
                scheme,
            )
    else:
        st.info("No exercises found. Seed the exercises table first.")
else:
    st.warning("Please log in on the Home page first.")