import streamlit as st
import psycopg
import pandas as pd
from supabase import create_client

# Read secrets
DATABASE_URL = st.secrets["DATABASE_URL"]
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def get_connection():
    return psycopg.connect(DATABASE_URL)

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def current_user_id():
    return st.session_state.get("user_id")

# --- Exercises ---
def add_exercise(exercise_name: str):
    uid = current_user_id()
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO exercises (user_id, name) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (uid, exercise_name),
        )
        conn.commit()

def get_exercises():
    uid = current_user_id()
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT name FROM exercises WHERE user_id = %s ORDER BY name", (uid,))
        return [r[0] for r in cur.fetchall()]

# --- Workouts ---
def log_workout(exercise_name, weight, sets, target_reps, achieved_reps, success, scheme, workout_date):
    uid = current_user_id()
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO workouts
               (user_id, exercise, date, weight, sets, target_reps, achieved_reps, success, scheme)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (uid, exercise_name, workout_date, weight, sets, target_reps, achieved_reps, success, scheme),
        )
        conn.commit()

def get_workouts():
    uid = current_user_id()
    conn = get_connection()
    return pd.read_sql_query(
        """SELECT date AS "Date", exercise AS "Exercise", weight AS "Weight",
                  sets AS "Sets", target_reps AS "Target Reps",
                  achieved_reps AS "Achieved Reps", success AS "Success", scheme AS "Scheme"
           FROM workouts
           WHERE user_id = %s
           ORDER BY date DESC""",
        conn,
        params=(uid,),
    )

def get_previous_workout(exercise_name: str):
    uid = current_user_id()
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """SELECT date, weight, sets, target_reps, achieved_reps, success, scheme
               FROM workouts
               WHERE user_id = %s AND exercise = %s
               ORDER BY date DESC LIMIT 1""",
            (uid, exercise_name),
        )
        row = cur.fetchone()
    if not row:
        return None
    return {
        "date": row[0],
        "weight": row[1],
        "sets": row[2],
        "target_reps": row[3],
        "achieved_reps": row[4],
        "success": row[5],
        "scheme": row[6],
    }

def suggest_next_workout(exercise_name: str):
    prev = get_previous_workout(exercise_name)
    if not prev:
        return {"weight": 20.0, "sets": 3, "target_reps": 5, "scheme": "5x5"}
    inc = 2.5 if prev["success"] else 0.0
    return {
        "weight": float(prev["weight"]) + inc,
        "sets": int(prev["sets"]),
        "target_reps": int(prev["target_reps"]),
        "scheme": prev["scheme"],
    }