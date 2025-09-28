import streamlit as st
import psycopg2
import pandas as pd
import requests
import os

# --- Supabase REST login ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

def login_user(email, password):
    url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
    headers = {"apikey": SUPABASE_KEY, "Content-Type": "application/json"}
    payload = {"email": email, "password": password}
    res = requests.post(url, headers=headers, json=payload)
    res.raise_for_status()
    return res.json()  # contains access_token + user object

# --- Database connection ---
conn = psycopg2.connect(
    host=os.environ.get("DB_HOST"),
    dbname=os.environ.get("DB_NAME"),
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASSWORD"),
    port=os.environ.get("DB_PORT", 5432),
)
cur = conn.cursor()

# --- Workout functions ---
def log_workout(exercise_name, weight, reps, user_id):
    try:
        cur.execute("SELECT id FROM exercises WHERE name = %s", (exercise_name,))
        exercise_id = cur.fetchone()
        if exercise_id:
            cur.execute(
                "INSERT INTO workouts (exercise_id, weight, reps, user_id) VALUES (%s, %s, %s, %s)",
                (exercise_id[0], weight, reps, user_id),
            )
            conn.commit()
            st.success("Workout logged!")
        else:
            st.error("Exercise not found.")
    except Exception as e:
        conn.rollback()
        st.error(f"Error: {e}")

def get_workouts(user_id):
    cur.execute("""
        SELECT w.workout_date, e.name, w.weight, w.reps
        FROM workouts w
        JOIN exercises e ON w.exercise_id = e.id
        WHERE w.user_id = %s
        ORDER BY w.workout_date DESC;
    """, (user_id,))
    rows = cur.fetchall()
    return pd.DataFrame(rows, columns=["Date", "Exercise", "Weight", "Reps"])

# --- Streamlit UI ---
st.title("🏋️ Weightlifting Tracker")

if "user" not in st.session_state:
    st.session_state.user = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "access_token" not in st.session_state:
    st.session_state.access_token = None

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
        st.session_state.user = None
        st.session_state.user_id = None
        st.session_state.access_token = None
        st.rerun()

    st.subheader("Log Workout")

    # Dropdown for exercises instead of free text
    cur.execute("SELECT name FROM exercises ORDER BY name;")
    exercise_names = [row[0] for row in cur.fetchall()]
    exercise = st.selectbox("Exercise", exercise_names)

    weight = st.number_input("Weight (kg)", min_value=0)
    reps = st.number_input("Reps", min_value=0)

    if st.button("Save Workout"):
        if st.session_state.user_id:
            log_workout(exercise, weight, reps, st.session_state.user_id)
        else:
            st.error("No user ID found in session.")

    st.subheader("Workout History")
    if st.session_state.user_id:
        df = get_workouts(st.session_state.user_id)
        if not df.empty:
            st.dataframe(df)
        else:
            st.info("No workouts logged yet.")