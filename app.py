import streamlit as st
from utils import login_user, ensure_session_keys

# Configure page
st.set_page_config(page_title="Weightlifting Tracker", page_icon="🏋️")

st.title("🏋️ Weightlifting Tracker")

# Ensure session state keys exist
ensure_session_keys()

# --- Login / Logout logic ---
if st.session_state.user is None:
    st.header("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Log in"):
        try:
            user_data = login_user(email, password)
            st.session_state.user = user_data["user"]
            st.session_state.user_id = user_data["user"]["id"]
            st.session_state.access_token = user_data["access_token"]
            st.success("Logged in!")
            st.rerun()
        except Exception as e:
            st.error(str(e))
else:
    st.success(f"Welcome {st.session_state.user['email']}")
    if st.button("Log out"):
        for key in ["user", "user_id", "access_token"]:
            st.session_state[key] = None
        st.rerun()

st.caption("Use the sidebar to navigate to Log Workout or Workout History.")