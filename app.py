import streamlit as st
from supabase import create_client, Client
from utils import ensure_session_keys, refresh_supabase_session, login_user

# --- Page config ---
st.set_page_config(page_title="Weightlifting Tracker", page_icon="🏋️")

st.title("🏋️ Weightlifting Tracker")

# --- Update notes for testers ---
st.success("""
Update to scheme control. Now Has 3 x 15, 3 x 10, 3 x 5 only. Suggestion logic updated accordingly.
For any further feedback, please reach out at: **Jordan.kennedy.leeds@googlemail.com**
""")

# --- Initialise Supabase client ---
supabase: Client = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# --- Ensure session keys exist ---
ensure_session_keys()

# --- Background auto-refresh every 30 minutes ---
# Requires: pip install streamlit-autorefresh
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=1800000, key="session_refresh")  # 30 min = 1,800,000 ms
except ImportError:
    st.warning("streamlit-autorefresh not installed. Background refresh disabled.")

# --- Refresh session if needed ---
refresh_supabase_session()

# --- Authentication logic ---
if st.session_state.user is None:
    st.header("Login / Sign Up")

    tab_login, tab_signup = st.tabs(["🔑 Log In", "🆕 Sign Up"])

    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Log in"):
            try:
                if login_user(email, password):
                    st.success(f"Logged in as {st.session_state.user['email']}")
                    st.rerun()
                else:
                    st.error("Invalid login credentials.")
            except Exception as e:
                st.error(f"Login failed: {e}")

    with tab_signup:
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        if st.button("Sign up"):
            try:
                res = supabase.auth.sign_up({"email": new_email, "password": new_password})
                if res.user:
                    st.success("Account created! Please check your email to confirm.")
                else:
                    st.error("Sign-up failed.")
            except Exception as e:
                st.error(f"Sign-up failed: {e}")

else:
    st.success(f"Welcome {st.session_state.user['email']}")
    if st.button("Log out"):
        for key in ["user", "user_id", "access_token", "refresh_token"]:
            st.session_state[key] = None
        st.rerun()

# --- Sidebar navigation ---
st.sidebar.title("Navigation")
st.sidebar.markdown(
    """
    - ➕ **Add Exercise**  
    - 💪 **Log Workout**  
    - 📜 **Workout History**  
    """
)
st.sidebar.caption("Pages are also listed automatically below.")

# --- Debug info (optional) ---
st.write("Current user_id in session:", st.session_state.get("user_id"))

st.caption("Use the sidebar to navigate between pages.")