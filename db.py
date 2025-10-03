import streamlit as st
import psycopg
import pandas as pd
from supabase import create_client

# --- Secrets ---
DATABASE_URL = st.secrets["DATABASE_URL"]
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

# --- Cached connections ---
@st.cache_resource
def get_connection():
    return psycopg.connect(DATABASE_URL)

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def current_user_id():
    uid = st.session_state.get("user_id")
    if not uid:
        raise RuntimeError("No user_id in session.")
    return uid

# ----------------- Exercises -----------------
def add_exercise(exercise_name: str):
    uid = current_user_id()
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO exercises (user_id, name)
            VALUES (%s, %s)
            ON CONFLICT (user_id, name) DO NOTHING
        """, (uid, exercise_name))
        conn.commit()

def get_exercises():
    uid = current_user_id()
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT name FROM exercises WHERE user_id = %s ORDER BY name", (uid,))
        return [r[0] for r in cur.fetchall()]

# ----------------- Workouts -----------------
def log_workout(exercise_name, weight, sets, target_reps, achieved_reps, success, scheme, workout_date):
    uid = current_user_id()
    conn = get_connection()
    with conn.cursor() as cur:
        # Look up exercise_id
        cur.execute("SELECT id FROM exercises WHERE user_id = %s AND name = %s", (uid, exercise_name))
        row = cur.fetchone()
        if not row:
            raise RuntimeError(f"Exercise '{exercise_name}' not found for user {uid}")
        exercise_id = row[0]

        cur.execute("""
            INSERT INTO workouts (user_id, exercise_id, workout_date, weight, sets, target_reps, achieved_reps, success, scheme)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (uid, exercise_id, workout_date, weight, sets, target_reps, achieved_reps, success, scheme))
        conn.commit()

def get_workouts():
    uid = current_user_id()
    conn = get_connection()
    return pd.read_sql_query("""
        SELECT w.workout_date AS "Date",
               e.name AS "Exercise",
               w.weight AS "Weight",
               w.sets AS "Sets",
               w.target_reps AS "Target Reps",
               w.achieved_reps AS "Achieved Reps",
               w.success AS "Success",
               w.scheme AS "Scheme"
        FROM workouts w
        JOIN exercises e ON w.exercise_id = e.id
        WHERE w.user_id = %s
        ORDER BY w.workout_date DESC
    """, conn, params=(uid,))

def get_previous_workout(exercise_name: str):
    uid = current_user_id()
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT w.workout_date, w.weight, w.sets, w.target_reps,
                   w.achieved_reps, w.success, w.scheme
            FROM workouts w
            JOIN exercises e ON w.exercise_id = e.id
            WHERE w.user_id = %s AND e.name = %s
            ORDER BY w.workout_date DESC
            LIMIT 1
        """, (uid, exercise_name))
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
    scheme_cycle = ["3 x 15", "3 x 10", "5 x 5"]

    # Map scheme strings to a canonical form
    scheme_aliases = {
        "3x15": "3 x 15",
        "3 x 15": "3 x 15",
        "3×15": "3 x 15",
        "3x10": "3 x 10",
        "3 x 10": "3 x 10",
        "3×10": "3 x 10",
        "5x5": "5 x 5",
        "5 x 5": "5 x 5",
        "5×5": "5 x 5",
    }

    if not prev:
        return {"weight": 20.0, "sets": 3, "target_reps": 15, "scheme": "3 x 15"}

    # Normalize previous scheme
    current_scheme = scheme_aliases.get(prev["scheme"], "3 x 15")
    idx = scheme_cycle.index(current_scheme)

    if prev["success"]:
        inc = 2.5
        next_scheme = current_scheme
    else:
        inc = 0.0
        next_scheme = scheme_cycle[(idx + 1) % len(scheme_cycle)]

    scheme_defaults = {
        "3 x 15": (3, 15),
        "3 x 10": (3, 10),
        "5 x 5": (5, 5),
    }
    sets, reps = scheme_defaults[next_scheme]

    return {
        "weight": float(prev["weight"]) + inc,
        "sets": sets,
        "target_reps": reps,
        "scheme": next_scheme,
    }