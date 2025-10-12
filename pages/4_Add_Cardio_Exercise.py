import streamlit as st
from db import add_cardio_exercise, get_cardio_exercises

st.set_page_config(page_title="Add Cardio Exercise", page_icon="➕")

st.title("➕ Add a New Cardio Exercise")

# --- Guard ---
if "user_id" not in st.session_state or not st.session_state["user_id"]:
    st.error("You must be signed in to manage cardio exercises.")
    st.stop()

# --- Form ---
with st.form("add_cardio_exercise_form"):
    name = st.text_input("Cardio exercise name")
    submitted = st.form_submit_button("Add Cardio Exercise")

    if submitted:
        if name.strip():
            add_cardio_exercise(name.strip())
            st.success(f"Added cardio exercise: {name}")
        else:
            st.error("Please enter a valid name.")

# --- Show current cardio exercises ---
st.subheader("Your cardio exercises")
exercises = get_cardio_exercises()
if exercises:
    st.write(exercises)
else:
    st.info("No cardio exercises added yet.")