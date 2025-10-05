import streamlit as st
from supabase import create_client

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def ensure_session_keys():
    """Guarantee required session keys exist."""
    if "user" not in st.session_state:
        st.session_state.user = None
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "access_token" not in st.session_state:
        st.session_state.access_token = None
    if "refresh_token" not in st.session_state:
        st.session_state.refresh_token = None

def login_user(email, password):
    """Log in with email/password and store tokens in session_state."""
    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
    if res.user:
        st.session_state.user = {"email": res.user.email, "id": res.user.id}
        st.session_state.user_id = res.user.id
        st.session_state.access_token = res.session.access_token
        st.session_state.refresh_token = res.session.refresh_token
        return True
    return False

def refresh_supabase_session():
    """
    Refresh the Supabase session if a refresh_token is available.
    Call this at the top of each page to keep users logged in.
    """
    if st.session_state.get("refresh_token"):
        try:
            res = supabase.auth.refresh_session(st.session_state["refresh_token"])
            if res and res.session:
                st.session_state.access_token = res.session.access_token
                st.session_state.refresh_token = res.session.refresh_token
                if res.user:
                    st.session_state.user = {"email": res.user.email, "id": res.user.id}
                    st.session_state.user_id = res.user.id
        except Exception as e:
            st.warning(f"Session refresh failed: {e}")