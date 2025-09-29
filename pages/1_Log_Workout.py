import streamlit as st
from utils import ensure_session_keys
from db import (
    get_exercises,
    log_workout,
    suggest_next_workout,
    get_starting_scheme,
    set_starting_scheme,
)

st.header("Log Workout")
ensure_session_keys()

def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

user_id = st.session_state.get("user_id")

if user_id:
    exercise_names = get_exercises(user_id)
    if exercise_names:
        exercise = st.selectbox("Exercise", exercise_names)

        if exercise:
            # Check if user has a starting scheme
            starting_scheme = get_starting_scheme(user_id, exercise)

            if not starting_scheme:
                choice = st.selectbox(
                    "Choose your starting rep range", ["5", "10", "15"], key="starting_range_choice"
                )
                if st.button("Set Starting Scheme"):
                    set_starting_scheme(user_id, exercise, f"3x{choice}")
                    st.success(f"Starting scheme set to 3x{choice}")
                    safe_rerun()
                st.info("Set a starting scheme to begin logging.")
                st.stop()

            st.info(f"Starting scheme for {exercise}: {starting_scheme}")

            # Fetch suggestion
            suggestion = None
            try:
                suggestion = suggest_next_workout(user_id, exercise)
            except Exception as e:
                st.warning(f"Could not fetch suggestion: {e}")

            if suggestion and isinstance(suggestion, dict):
                st.session_state.suggested = suggestion
                st.info(
                    f"Suggested: {suggestion.get('scheme', 'N/A')} at {suggestion.get('weight', 0)} kg "
                    f"({suggestion.get('sets', 3)} sets × {suggestion.get('target_reps', 10)} reps)"
                )
            else:
                st.warning("No suggestion available for this exercise yet.")
                st.session_state.suggested = {}

            # Inputs (prefilled from suggestion)
            suggested = st.session_state.get("suggested", {})
            weight = st.number_input(
                "Weight (kg)", min_value=0, step=1, value=int(suggested.get("weight", 0))
            )
            sets = st.number_input(
                "Sets", min_value=1, step=1, value=int(suggested.get("sets", 3))
            )
            target_reps = st.number_input(
                "Target Reps", min_value=1, step=1, value=int(suggested.get("target_reps", 10))
            )
            achieved_reps = st.number_input("Achieved Reps", min_value=0, step=1, value=0)
            success = st.checkbox("Success (hit target reps?)", value=False)

            # Scheme defaults to suggested or sets×reps
            scheme = suggested.get("scheme") or f"{sets}x{target_reps}"

            if st.button("Save Workout"):
                log_workout(
                    exercise,
                    weight,
                    sets,
                    target_reps,
                    achieved_reps,
                    success,
                    user_id,
                    scheme,
                )
    else:
        st.info("No exercises found. Add your first exercise on the 'Add Exercise' page.")
else:
    st.warning("Please log in on the Home page first.")