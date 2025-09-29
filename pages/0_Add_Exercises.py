import streamlit as st
from utils import ensure_session_keys
from db import add_exercise, get_exercises

st.header("Add Exercise")
ensure_session_keys()

user_id = st.session_state.get("user_id")

if user_id:
    new_ex = st.text_input("New exercise name")
    if st.button("Add Exercise") and new_ex.strip():
        add_exercise(user_id, new_ex)

    st.subheader("Your exercises")
    exercises = get_exercises(user_id)
    if exercises:
        st.write(exercises)
    else:
        st.info("No exercises added yet.")
else:
    st.warning("Please log in on the Home page first.")