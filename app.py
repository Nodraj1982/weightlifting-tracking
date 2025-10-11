import streamlit as st
import pathlib
from supabase import create_client, Client
import datetime
from streamlit_cookies_manager import EncryptedCookieManager

# --- Serve static files via query params ---
query = st.query_params.get("file")

if query == "manifest":
    st.json(pathlib.Path("manifest.json").read_text())
    st.stop()

if query == "sw":
    st.write(pathlib.Path("service-worker.js").read_text())
    st.stop()

if query == "icon192":
    st.image("icon-192.png")
    st.stop()

if query == "icon512":
    st.image("icon-512.png")
    st.stop()

# --- Page config ---
st.set_page_config(page_title="Jellybean: One Sweet Place", page_icon="🍬")
st.title("🍬 Jellybean")
st.caption("One Sweet Place")

# --- Update notes for testers ---
st.success("""
Rebrand of app and tidy up of UI to take into account new features.
For any further feedback, please reach out at: **Jordan.kennedy.leeds@googlemail.com**
""")

# --- Initialise Supabase client ---
supabase: Client = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# --- Initialise cookie manager ---
cookies = EncryptedCookieManager(prefix="supabase", password="a-long-random-secret")
if not cookies.ready():
    st.stop()

# --- Ensure session state keys exist ---
for key in ["access_token", "refresh_token", "user_email", "user_id"]:
    if key not in st.session_state:
        st.session_state[key] = None

# --- Try to restore from cookie ---
if not st.session_state["refresh_token"]:
    token = cookies.get("refresh_token")
    if token:
        try:
            refreshed = supabase.auth.refresh_session(token)  # pass string, not dict
            if refreshed.session:
                st.session_state["access_token"] = refreshed.session.access_token
                st.session_state["refresh_token"] = refreshed.session.refresh_token
                st.session_state["user_email"] = refreshed.user.email
                st.session_state["user_id"] = refreshed.user.id   # ✅ added
                st.write("Session restored from cookie")
        except Exception as e:
            st.error(f"Failed to restore session: {e}")

# --- Background auto-refresh every 30 minutes ---
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=1800000, key="session_refresh")  # 30 min
except ImportError:
    st.warning("streamlit-autorefresh not installed. Background refresh disabled.")

# --- Refresh session if needed ---
def refresh_session():
    if st.session_state["refresh_token"]:
        try:
            refreshed = supabase.auth.refresh_session(st.session_state["refresh_token"])
            if refreshed.session:
                st.session_state["access_token"] = refreshed.session.access_token
                st.session_state["refresh_token"] = refreshed.session.refresh_token
                st.session_state["user_email"] = refreshed.user.email
                st.session_state["user_id"] = refreshed.user.id   # ✅ added
                cookies["refresh_token"] = refreshed.session.refresh_token
                cookies.save()
        except Exception as e:
            st.error(f"Session refresh failed: {e}")

refresh_session()

# --- Authentication logic ---
if not st.session_state["user_email"]:
    st.header("Login / Sign Up")

    tab_login, tab_signup = st.tabs(["🔑 Log In", "🆕 Sign Up"])

    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Log in"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                if res.user:
                    st.session_state["access_token"] = res.session.access_token
                    st.session_state["refresh_token"] = res.session.refresh_token
                    st.session_state["user_email"] = res.user.email
                    st.session_state["user_id"] = res.user.id   # ✅ added
                    cookies["refresh_token"] = res.session.refresh_token
                    cookies.save()
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
    st.success(f"Welcome {st.session_state['user_email']}")
    if st.button("Log out"):
        for key in ["access_token", "refresh_token", "user_email", "user_id"]:
            st.session_state[key] = None
        cookies["refresh_token"] = ""
        cookies.save()
        st.rerun()

# --- Debug info (optional) ---
if st.session_state.get("user_email") == "jordan.kennedy.leeds@googlemail.com":
    st.write("Current user email:", st.session_state.get("user_email"))
    st.write("Current user id:", st.session_state.get("user_id"))

st.caption("Use the sidebar to navigate between pages.")