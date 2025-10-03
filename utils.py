import os
import requests
import streamlit as st

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

def login_user(email, password):
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("Supabase URL/Key not configured in secrets.")
    url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
    headers = {"apikey": SUPABASE_KEY, "Content-Type": "application/json"}
    payload = {"email": email, "password": password}
    res = requests.post(url, headers=headers, json=payload)
    res.raise_for_status()
    return res.json()

def ensure_session_keys():
    for key in ["user", "user_id", "access_token"]:
        if key not in st.session_state:
            st.session_state[key] = None