import os
import psycopg2
import pandas as pd
import streamlit as st

# --- Database connection ---
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is missing.")

conn = psycopg2.connect(DATABASE_URL)

# --- Configurable increments per exercise ---
INCREMENTS = {
    "Bench Press": 2.5,
    "Squat": 5.0,
    "Deadlift": 5.0,
    "Overhead Press": 2.5,
    "Barbell Row": 2.5,
}

def get_increment(exercise_name: str) -> float:
    return INCREMENTS.get(exercise_name, 2.5)

# --- Exercise functions ---
def get_exercises():
    with conn.cursor() as cur:
        cur.execute("SELECT name FROM exercises ORDER BY name;")
        return [row[0] for row in cur.fetchall()]

# --- User exercise settings ---
def get_starting_scheme(user_id, exercise_name):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT s.starting_scheme
            FROM user_exercise_settings s
            JOIN exercises e ON s.exercise_id = e.id
            WHERE s.user_id = %s AND e.name = %s
        """, (user_id, exercise_name))
        row = cur.fetchone()
        return row[0] if row else None

def set_starting_scheme(user_id, exercise_name, scheme):
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM exercises WHERE name = %s", (exercise_name,))
        exercise_id = cur.fetchone()[0]
        cur.execute("""
            INSERT INTO user_exercise_settings (user_id, exercise_id, starting_scheme)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, exercise_id) DO UPDATE
            SET starting_scheme = EXCLUDED.starting_scheme
        """, (user_id, exercise_id, scheme))
        conn.commit()

# --- Workout functions ---
def log_workout(exercise_name, weight, sets, target_reps, achieved_reps, success, user_id, scheme):
    """Insert a workout into the database, including sets and progression fields."""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM exercises WHERE name = %s", (exercise_name,))
            exercise_id = cur.fetchone()
            if not exercise_id:
                st.error("Exercise not found.")
                return
            cur.execute(
                """
                INSERT INTO workouts (exercise_id, weight, sets, target_reps, achieved_reps, success, user_id, scheme)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (exercise_id[0], weight, sets, target_reps, achieved_reps, success, user_id, scheme),
            )
            conn.commit()
            st.success("Workout logged!")
    except Exception as e:
        conn.rollback()
        st.error(f"Error: {e}")

def get_workouts(user_id):
    """Fetch workouts for a given user, including sets and progression fields."""
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
    """Suggest the next workout based on last logged set for this exercise."""
    increment = get_increment(exercise_name)

    # Check if user has a starting scheme set
    starting_scheme = get_starting_scheme(user_id, exercise_name)

    with conn.cursor() as cur:
        cur.execute("""
            SELECT w.weight, w.target_reps, w.success, w.scheme
            FROM workouts w
            JOIN exercises e ON w.exercise_id = e.id
            WHERE w.user_id = %s AND e.name = %s
            ORDER BY w.workout_date DESC
            LIMIT 1;
        """, (user_id, exercise_name))
        last = cur.fetchone()

    if not last:
        # No history → use chosen starting scheme
        if starting_scheme:
            reps = int(starting_scheme.split("x")[1])
            return {"scheme": starting_scheme, "target_reps": reps, "weight": 20, "sets": 3}
        else:
            # fallback if user never set one
            return {"scheme": "3x15", "target_reps": 15, "weight": 20, "sets": 3}

    last_weight, last_target, last_success, last_scheme = last

    if last_scheme == "3x15":
        if last_success:
            return {"scheme": "3x15", "target_reps": 15, "weight": last_weight + increment, "sets": 3}
        else:
            return {"scheme": "3x10", "target_reps": 10, "weight": last_weight, "sets": 3}

    if last_scheme == "3x10":
        if last_success:
            return {"scheme": "3x10", "target_reps": 10, "weight": last_weight + increment, "sets": 3}
        else:
            return {"scheme": "3x5", "target_reps": 5, "weight": last_weight, "sets": 3}

    if last_scheme == "3x5":
        if last_success:
            return {"scheme": "3x5", "target_reps": 5, "weight": last_weight + increment, "sets": 3}
        else:
            return {"scheme": "3x15", "target_reps": 15, "weight": max(0, last_weight - increment), "sets": 3}