import streamlit as st
import psycopg2
import pandas as pd
import requests

# -------------------------------
# Supabase REST Auth setup
# -------------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

def login_user(email, password):
    url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
    headers = {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "email": email,
        "password": password
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(response.json().get("error_description", "Login failed"))

# -------------------------------
# Session state for login
# -------------------------------
if "user" not in st.session_state:
    st.session_state.user = None

# -------------------------------
# Login / Logout UI
# -------------------------------
if st.session_state.user is None:
    st.title("🏋️ Weightlifting Tracker")
    st.header("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Log in"):
        try:
            user_data = login_user(email, password)
            st.session_state.user = user_data
            st.success("Logged in!")
            st.experimental_rerun()
        except Exception as e:
            st.error(str(e))
else:
    st.title("🏋️ Weightlifting Tracker")
    st.success(f"Welcome {st.session_state.user.get('user', {}).get('email', 'User')}")
    if st.button("Log out"):
        st.session_state.user = None
        st.experimental_rerun()

    # -------------------------------
    # Database connection
    # -------------------------------
    @st.cache_resource
    def get_connection():
        try:
            return psycopg2.connect(st.secrets["DB_URI"])
        except Exception as e:
            st.error(f"Database connection failed: {e}")
            return None

    conn = get_connection()
    cur = conn.cursor()

    # -------------------------------
    # Helper functions
    # -------------------------------
    def create_tables():
        cur.execute("""
            CREATE TABLE IF NOT EXISTS exercises (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS workouts (
                id SERIAL PRIMARY KEY,
                exercise_id INT REFERENCES exercises(id),
                weight NUMERIC,
                reps INT,
                workout_date DATE DEFAULT CURRENT_DATE
            );
        """)
        conn.commit()

    def add_exercise(name):
        try:
            cur.execute("INSERT INTO exercises (name) VALUES (%s)", (name,))
            conn.commit()
            st.success(f"Exercise '{name}' added.")
        except Exception as e:
            conn.rollback()
            st.error(f"Error: {e}")

    def log_workout(exercise_name, weight, reps):
        try:
            cur.execute("SELECT id FROM exercises WHERE name = %s", (exercise_name,))
            exercise_id = cur.fetchone()
            if exercise_id:
                cur.execute(
                    "INSERT INTO workouts (exercise_id, weight, reps) VALUES (%s, %s, %s)",
                    (exercise_id[0], weight, reps),
                )
                conn.commit()
                st.success("Workout logged!")
            else:
                st.error("Exercise not found.")
        except Exception as e:
            conn.rollback()
            st.error(f"Error: {e}")

    def get_workouts():
        cur.execute("""
            SELECT w.workout_date, e.name, w.weight, w.reps
            FROM workouts w
            JOIN exercises e ON w.exercise_id = e.id
            ORDER BY w.workout_date DESC;
        """)
        rows = cur.fetchall()
        return pd.DataFrame(rows, columns=["Date", "Exercise", "Weight", "Reps"])

    # -------------------------------
    # Streamlit UI
    # -------------------------------
    create_tables()

    menu = ["Add Exercise", "Log Workout", "View History"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Add Exercise":
        st.subheader("Add a New Exercise")
        exercise_name = st.text_input("Exercise name")
        if st.button("Add"):
            if exercise_name.strip():
                add_exercise(exercise_name.strip())
            else:
                st.warning("Please enter a valid exercise name.")

    elif choice == "Log Workout":
        st.subheader("Log a Workout")
        cur.execute("SELECT name FROM exercises ORDER BY name;")
        exercises = [row[0] for row in cur.fetchall()]
        if exercises:
            exercise = st.selectbox("Exercise", exercises)
            weight = st.number_input("Weight (kg)", min_value=0.0, step=2.5)
            reps = st.number_input("Reps", min_value=1, step=1)
            if st.button("Log Workout"):
                log_workout(exercise, weight, reps)
        else:
            st.info("No exercises found. Add one first.")

    elif choice == "View History":
        st.subheader("Workout History")
        df = get_workouts()
        if not df.empty:
            st.dataframe(df)
        else:
            st.info("No workouts logged yet.")