import psycopg
import streamlit as st

# --- Database connection ---
DATABASE_URL = st.secrets["DATABASE_URL"]

@st.cache_resource
def get_connection():
    return psycopg.connect(DATABASE_URL)

conn = get_connection()


# --- Example helper functions ---

def add_exercise(name: str):
    """Insert a new exercise into the database."""
    with conn.cursor() as cur:
        cur.execute("INSERT INTO exercises (name) VALUES (%s)", (name,))
        conn.commit()


def get_exercises():
    """Fetch all exercise names."""
    with conn.cursor() as cur:
        cur.execute("SELECT name FROM exercises ORDER BY name;")
        rows = cur.fetchall()
    return [r[0] for r in rows]


def get_previous_workout(exercise_name: str):
    """Fetch the most recent workout for a given exercise."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT date, weight, sets, target_reps, achieved_reps, success, scheme
            FROM workouts
            WHERE exercise = %s
            ORDER BY date DESC
            LIMIT 1;
            """,
            (exercise_name,),
        )
        row = cur.fetchone()
    if row:
        return {
            "date": row[0],
            "weight": row[1],
            "sets": row[2],
            "target_reps": row[3],
            "achieved_reps": row[4],
            "success": row[5],
            "scheme": row[6],
        }
    return None