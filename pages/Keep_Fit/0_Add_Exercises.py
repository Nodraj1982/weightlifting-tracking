import streamlit as st
from db import add_exercise, get_exercises

st.set_page_config(page_title="Add Exercise", page_icon="➕")

st.title("➕ Add a New Exercise")

# --- Guard: must be signed in ---
if "user_id" not in st.session_state or not st.session_state["user_id"]:
    st.error("You must be signed in to manage exercises.")
    st.stop()

# --- Add exercise form ---
with st.form("add_exercise_form"):
    exercise_name = st.text_input("Exercise name")
    submitted = st.form_submit_button("Add Exercise")

    if submitted:
        if exercise_name.strip():
            add_exercise(exercise_name)
        else:
            st.error("Please enter a valid exercise name.")

# --- Show current exercises ---
st.subheader("Your exercises")
exercises = get_exercises()
if exercises:
    st.write(exercises)
else:
    st.info("No exercises added yet.")