import os
import psycopg2
import pandas as pd
import streamlit as st

# --- Database connection ---
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is missing.")

conn = psycopg2.connect(DATABASE_URL)

# --- Exercise functions ---
def get_exercises():
    with conn.cursor() as cur:
        cur.execute("SELECT name FROM exercises ORDER BY name;")
        return [row[0] for row in cur.fetchall()]

# --- Workout functions ---
def log_workout(exercise_name, weight, target_reps, achieved_reps, success, user_id, scheme):
    """Insert a workout into the database, including progression fields."""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM exercises WHERE name = %s", (exercise_name,))
            exercise_id = cur.fetchone()
            if not exercise_id:
                st.error("Exercise not found.")
                return
            cur.execute(
                """
                INSERT INTO workouts (exercise_id, weight, target_reps, achieved_reps, success, user_id, scheme)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (exercise_id[0], weight, target_reps, achieved_reps, success, user_id, scheme),
            )
            conn.commit()
            st.success("Workout logged!")
    except Exception as e:
        conn.rollback()
        st.error(f"Error: {e}")

def get_workouts(user_id):
    """Fetch workouts for a given user (basic version)."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT w.workout_date, e.name, w.weight, w.reps
            FROM workouts w
            JOIN exercises e ON w.exercise_id = e.id
            WHERE w.user_id = %s
            ORDER BY w.workout_date DESC;
        """, (user_id,))
        rows = cur.fetchall()
    return pd.DataFrame(rows, columns=["Date", "Exercise", "Weight", "Reps"])

def suggest_next_workout(user_id, exercise_name):
    """Suggest the next workout based on last logged set for this exercise."""
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
        # No history → start at 3x15 with a baseline weight
        return {"scheme": "3x15", "target_reps": 15, "weight": 20}

    last_weight, last_target, last_success, last_scheme = last

    if last_scheme == "3x15":
        if last_success:
            return {"scheme": "3x15", "target_reps": 15, "weight": last_weight + 2.5}
        else:
            return {"scheme": "3x10", "target_reps": 10, "weight": last_weight}

    if last_scheme == "3x10":
        if last_success:
            return {"scheme": "3x10", "target_reps": 10, "weight": last_weight + 2.5}
        else:
            return {"scheme": "3x5", "target_reps": 5, "weight": last_weight}

    if last_scheme == "3x5":
        if last_success:
            return {"scheme": "3x5", "target_reps": 5, "weight": last_weight + 2.5}
        else:
            # Reset to 3x15, but drop slightly (second-best weight)
            return {"scheme": "3x15", "target_reps": 15, "weight": max(0, last_weight - 2.5)}