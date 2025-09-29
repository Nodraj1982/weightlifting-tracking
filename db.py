import os
import psycopg2
import pandas as pd
import streamlit as st

# Get connection string from environment (Streamlit secrets inject this)
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is missing.")

# Create one global connection
conn = psycopg2.connect(DATABASE_URL)

def get_exercises():
    with conn.cursor() as cur:
        cur.execute("SELECT name FROM exercises ORDER BY name;")
        return [row[0] for row in cur.fetchall()]

def log_workout(exercise_name, weight, reps, user_id):
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM exercises WHERE name = %s", (exercise_name,))
            exercise_id = cur.fetchone()
            if not exercise_id:
                st.error("Exercise not found.")
                return
            cur.execute(
                "INSERT INTO workouts (exercise_id, weight, reps, user_id) VALUES (%s, %s, %s, %s)",
                (exercise_id[0], weight, reps, user_id),
            )
            conn.commit()
            st.success("Workout logged!")
    except Exception as e:
        conn.rollback()
        st.error(f"Error: {e}")

def get_workouts(user_id):
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