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
    """
    Insert a workout into the database, including progression fields.
    """
    try:
        with conn.cursor() as cur:
            # Look up exercise_id
            cur.execute("SELECT id FROM exercises WHERE name = %s", (exercise_name,))
            exercise_id = cur.fetchone()
            if not exercise_id:
                st.error("Exercise not found.")
                return

            # Insert workout row
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
    """
    Fetch workouts for a given user.
    (Note: we’ll extend this later to include scheme once the UI is updated.)
    """
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