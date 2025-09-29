import os
import psycopg2
import pandas as pd
import streamlit as st

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is missing.")
conn = psycopg2.connect(DATABASE_URL)

INCREMENTS = {
    "Bench Press": 2.5,
    "Squat": 5.0,
    "Deadlift": 5.0,
    "Overhead Press": 2.5,
    "Barbell Row": 2.5,
}
def get_increment(exercise_name: str) -> float:
    return INCREMENTS.get(exercise_name, 2.5)

# --- Exercise management ---
def add_exercise(user_id, name):
    cleaned = name.strip()
    if not cleaned:
        st.error("Exercise name cannot be empty.")
        return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO exercises (name, user_id)
                VALUES (%s, %s)
                ON CONFLICT (user_id, name) DO NOTHING
                RETURNING id;
            """, (cleaned, user_id))
            row = cur.fetchone()
            conn.commit()
            if row:
                st.success(f"Exercise '{cleaned}' added.")
            else:
                st.info(f"Exercise '{cleaned}' already exists for this user.")
    except Exception as e:
        conn.rollback()
        st.error(f"Error adding exercise: {e}")

def get_exercises(user_id):
    with conn.cursor() as cur:
        cur.execute("SELECT name FROM exercises WHERE user_id = %s ORDER BY name;", (user_id,))
        return [row[0] for row in cur.fetchall()]

def _get_exercise_id_for_user(user_id, exercise_name):
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM exercises WHERE user_id = %s AND name = %s", (user_id, exercise_name))
        row = cur.fetchone()
        return row[0] if row else None

# --- Starting scheme ---
def get_starting_scheme(user_id, exercise_name):
    ex_id = _get_exercise_id_for_user(user_id, exercise_name)
    if not ex_id:
        return None
    with conn.cursor() as cur:
        cur.execute("""
            SELECT starting_scheme
            FROM user_exercise_settings
            WHERE user_id = %s AND exercise_id = %s
        """, (user_id, ex_id))
        row = cur.fetchone()
        return row[0] if row else None

def set_starting_scheme(user_id, exercise_name, scheme):
    ex_id = _get_exercise_id_for_user(user_id, exercise_name)
    if not ex_id:
        st.error("Exercise not found for this user.")
        return
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO user_exercise_settings (user_id, exercise_id, starting_scheme)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, exercise_id) DO UPDATE
            SET starting_scheme = EXCLUDED.starting_scheme
        """, (user_id, ex_id, scheme))
        conn.commit()

# --- Workouts ---
def log_workout(exercise_name, weight, sets, target_reps, achieved_reps, success, user_id, scheme):
    try:
        ex_id = _get_exercise_id_for_user(user_id, exercise_name)
        if not ex_id:
            st.error("Exercise not found for this user. Add it first.")
            return
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO workouts (exercise_id, weight, sets, target_reps, achieved_reps, success, user_id, scheme)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (ex_id, weight, sets, target_reps, achieved_reps, success, user_id, scheme))
            conn.commit()
            st.success("Workout logged!")
    except Exception as e:
        conn.rollback()
        st.error(f"Error logging workout: {e}")

def get_workouts(user_id):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT w.workout_date, e.name, w.weight, w.sets, w.target_reps, w.achieved_reps, w.success, w.scheme
            FROM workouts w
            JOIN exercises e ON w.exercise_id = e.id
            WHERE w.user_id = %s
            ORDER BY w.workout_date DESC;
        """, (user_id,))
        rows = cur.fetchall()
    return pd.DataFrame(
        rows,
        columns=["Date", "Exercise", "Weight", "Sets", "Target Reps", "Achieved Reps", "Success", "Scheme"]
    )

def suggest_next_workout(user_id, exercise_name):
    increment = get_increment(exercise_name)
    starting_scheme = get_starting_scheme(user_id, exercise_name)

    with conn.cursor() as cur:
        cur.execute("""
            SELECT w.weight, w.target_reps, w.success, w.scheme
            FROM workouts w
            JOIN exercises e ON w.exercise_id = e.id
            WHERE w.user_id = %s AND e.user_id = %s AND e.name = %s
            ORDER BY w.workout_date DESC
            LIMIT 1;
        """, (user_id, user_id, exercise_name))
        last = cur.fetchone()

    if not last:
        if starting_scheme:
            reps = int(starting_scheme.split("x")[1])
            return {"scheme": starting_scheme, "target_reps": reps, "weight": 20, "sets": 3}
        else:
            return {"scheme": "3x15", "target_reps": 15, "weight": 20, "sets": 3}

    last_weight, last_target, last_success, last_scheme = last

    if last_scheme == "3x15":
        return {"scheme": "3x15" if last_success else "3x10",
                "target_reps": 15 if last_success else 10,
                "weight": last_weight + increment if last_success else last_weight,
                "sets": 3}
    if last_scheme == "3x10":
        return {"scheme": "3x10" if last_success else "3x5",
                "target_reps": 10 if last_success else 5,
                "weight": last_weight + increment if last_success else last_weight,
                "sets": 3}
    if last_scheme == "3x5":
        return {"scheme": "3x5" if last_success else "3x15",
                "target_reps": 5 if last_success else 15,
                "weight": last_weight + increment if last_success else max(0, last_weight - increment),
                "sets": 3}

    return {"scheme": starting_scheme or "3x10", "target_reps": last_target or 10, "weight": last_weight or 20, "sets": 3}