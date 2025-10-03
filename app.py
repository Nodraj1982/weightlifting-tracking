import streamlit as st
from supabase import create_client, Client
from utils import ensure_session_keys

# --- Page config ---
st.set_page_config(page_title="Weightlifting Tracker", page_icon="🏋️")

st.title("🏋️ Weightlifting Tracker")

# --- Initialise Supabase client ---
supabase: Client = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# --- Ensure session keys exist ---
ensure_session_keys()

# --- Authentication logic ---
if st.session_state.user is None:
    st.header("Login / Sign Up")

    tab_login, tab_signup = st.tabs(["🔑 Log In", "🆕 Sign Up"])

    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Log in"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                if res.user:
                    st.session_state.user = {"email": res.user.email, "id": res.user.id}
                    st.session_state.user_id = res.user.id
                    st.success(f"Logged in as {res.user.email}")
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
        for key in ["user", "user_id", "access_token"]:
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