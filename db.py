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
            ORDER BY w.created_at DESC
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

    scheme_cycle = ["3 x 15", "3 x 10", "3 x 5"]

    if not prev:
        return {"weight": 20.0, "sets": 3, "target_reps": 15, "scheme": "3 x 15"}

    scheme_aliases = {
        "3x15": "3 x 15", "3 x 15": "3 x 15", "3×15": "3 x 15",
        "3x10": "3 x 10", "3 x 10": "3 x 10", "3×10": "3 x 10",
        "3x5": "3 x 5", "3 x 5": "3 x 5", "3×5": "3 x 5",
    }
    
    current_scheme = scheme_aliases.get(str(prev["scheme"]).strip(), "3 x 15")
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
        "3 x 5": (3, 5),
    }
    sets, reps = scheme_defaults[next_scheme]

    return {
        "weight": float(prev["weight"]) + inc,
        "sets": sets,
        "target_reps": reps,
        "scheme": next_scheme,
    }

# ----------------- Cardio Workouts -----------------
def log_cardio(workout_type, time_minutes, distance_km, difficulty_level, workout_date):
    uid = current_user_id()
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO cardio_workouts (user_id, workout_type, workout_date, time_minutes, distance_km, difficulty_level)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (uid, workout_type, workout_date, time_minutes, distance_km, difficulty_level))
        conn.commit()

def get_cardio_workouts():
    uid = current_user_id()
    conn = get_connection()
    return pd.read_sql_query("""
        SELECT workout_date AS "Date",
               workout_type AS "Workout Type",
               time_minutes AS "Time (min)",
               distance_km AS "Distance (km)",
               difficulty_level AS "Difficulty"
        FROM cardio_workouts
        WHERE user_id = %s
        ORDER BY workout_date DESC
    """, conn, params=(uid,))

def get_last_cardio(workout_type: str):
    uid = current_user_id()
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT workout_date, time_minutes, distance_km, difficulty_level
            FROM cardio_workouts
            WHERE user_id = %s AND workout_type = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (uid, workout_type))
        row = cur.fetchone()
    if not row:
        return None
    return {
        "date": row[0],
        "time": row[1],
        "distance": row[2],
        "difficulty": row[3],
    }

def add_cardio_exercise(name: str):
    uid = current_user_id()
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO cardio_exercises (user_id, name)
            VALUES (%s, %s)
            ON CONFLICT (user_id, name) DO NOTHING
        """, (uid, name))
        conn.commit()

def get_cardio_exercises():
    uid = current_user_id()
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT name FROM cardio_exercises WHERE user_id = %s ORDER BY name", (uid,))
        return [r[0] for r in cur.fetchall()]

# ----------------- Optional: family display names -----------------
def get_family_display_name(email: str) -> str:
    """
    Map emails to friendly display names (e.g., 'Mum', 'Jordan').
    Replace or extend this as needed, or wire to a table later.
    """
    aliases = {
        # "someone@example.com": "Mum",
        # "jordan.kennedy.leeds@googlemail.com": "Jordan",
    }
    return aliases.get(email, email)

# ----------------- Pips & NYT Games -----------------

def log_pips_score(difficulty: str, time_seconds: int, puzzle_date):
    """
    Log or update the current user's Pips score for a given difficulty and date.
    Stores raw seconds in the database.
    """
    uid = current_user_id()
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO pips_scores (user_id, puzzle_date, difficulty, time_seconds)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, puzzle_date, difficulty) DO UPDATE
            SET time_seconds = EXCLUDED.time_seconds
        """, (uid, puzzle_date, difficulty, time_seconds))
        conn.commit()


def log_nyt_score(game: str, score: int, puzzle_date, notes: str = None):
    """
    Log or update the current user's score for a generic NYT game
    (Wordle, Connections, Spelling Bee).
    """
    uid = current_user_id()
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO nyt_scores (user_id, game, puzzle_date, score, notes)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (user_id, game, puzzle_date) DO UPDATE
            SET score = EXCLUDED.score,
                notes = EXCLUDED.notes
        """, (uid, game, puzzle_date, score, notes))
        conn.commit()


# --- Helper to format seconds into MM:SS ---
def format_time(seconds: int) -> str:
    if seconds is None:
        return ""
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes}:{secs:02d}"


def get_pips_daily_leaderboard(puzzle_date):
    """
    Return daily leaderboards for easy, medium, hard, and overall.
    Each DataFrame has columns: Name, time (MM:SS), points.
    """
    conn = get_connection()
    results = {}

    # Per-difficulty leaderboards
    for diff in ["easy", "medium", "hard"]:
        query = """
        WITH ranked AS (
            SELECT s.user_id,
                   COALESCE(f.display_name, u.email) AS name,
                   s.time_seconds,
                   RANK() OVER (ORDER BY s.time_seconds ASC) AS rnk
            FROM pips_scores s
            JOIN auth.users u ON s.user_id = u.id
            LEFT JOIN family_members f ON u.id = f.user_id
            WHERE s.puzzle_date = %s AND s.difficulty = %s
        )
        SELECT name,
               time_seconds,
               CASE rnk WHEN 1 THEN 3
                        WHEN 2 THEN 2
                        WHEN 3 THEN 1
                        ELSE 0 END AS points
        FROM ranked
        ORDER BY rnk
        """
        df = pd.read_sql_query(query, conn, params=(puzzle_date, diff))
        if not df.empty:
            df["time"] = df["time_seconds"].apply(format_time)
            df = df[["name", "time", "points"]]
        results[diff] = df

    # Overall leaderboard (sum across difficulties)
    query = """
    WITH totals AS (
        SELECT s.user_id,
               COALESCE(f.display_name, u.email) AS name,
               SUM(s.time_seconds) AS total_time
        FROM pips_scores s
        JOIN auth.users u ON s.user_id = u.id
        LEFT JOIN family_members f ON u.id = f.user_id
        WHERE s.puzzle_date = %s
        GROUP BY s.user_id, name
    ),
    ranked AS (
        SELECT name,
               total_time,
               RANK() OVER (ORDER BY total_time ASC) AS rnk
        FROM totals
    )
    SELECT name,
           total_time,
           CASE rnk WHEN 1 THEN 3
                    WHEN 2 THEN 2
                    WHEN 3 THEN 1
                    ELSE 0 END AS points
    FROM ranked
    ORDER BY rnk
    """
    df = pd.read_sql_query(query, conn, params=(puzzle_date,))
    if not df.empty:
        df["time"] = df["total_time"].apply(format_time)
        df = df[["name", "time", "points"]]
    results["overall"] = df

    return results


def get_pips_points_leaderboard(period="weekly"):
    """
    Aggregate daily points into weekly, monthly, or all-time leaderboards.
    Includes easy, medium, hard, and overall points.
    Returns columns: Name, period, total_points.
    """
    conn = get_connection()

    if period == "weekly":
        group_expr = "DATE_TRUNC('week', puzzle_date)"
    elif period == "monthly":
        group_expr = "DATE_TRUNC('month', puzzle_date)"
    elif period == "all":
        group_expr = "'all-time'"
    else:
        raise ValueError("Invalid period")

    query = f"""
    -- Per-difficulty points
    WITH ranked AS (
        SELECT s.user_id,
               COALESCE(f.display_name, u.email) AS name,
               s.puzzle_date,
               s.difficulty,
               RANK() OVER (
                   PARTITION BY s.difficulty, s.puzzle_date
                   ORDER BY s.time_seconds ASC
               ) AS rnk
        FROM pips_scores s
        JOIN auth.users u ON s.user_id = u.id
        LEFT JOIN family_members f ON u.id = f.user_id
    ),
    diff_points AS (
        SELECT name,
               puzzle_date,
               difficulty,
               CASE rnk WHEN 1 THEN 3
                        WHEN 2 THEN 2
                        WHEN 3 THEN 1
                        ELSE 0 END AS points
        FROM ranked
    ),
    -- Overall points (sum across difficulties per day)
    overall AS (
        SELECT s.user_id,
               COALESCE(f.display_name, u.email) AS name,
               s.puzzle_date,
               SUM(s.time_seconds) AS total_time,
               RANK() OVER (
                   PARTITION BY s.puzzle_date
                   ORDER BY SUM(s.time_seconds) ASC
               ) AS rnk
        FROM pips_scores s
        JOIN auth.users u ON s.user_id = u.id
        LEFT JOIN family_members f ON u.id = f.user_id
        GROUP BY s.user_id, name, s.puzzle_date
    ),
    overall_points AS (
        SELECT name,
               puzzle_date,
               'overall' AS difficulty,
               CASE rnk WHEN 1 THEN 3
                        WHEN 2 THEN 2
                        WHEN 3 THEN 1
                        ELSE 0 END AS points
        FROM overall
    ),
    all_points AS (
        SELECT * FROM diff_points
        UNION ALL
        SELECT * FROM overall_points
    )
    SELECT name,
           {group_expr} AS period,
           SUM(points) AS total_points
    FROM all_points
    GROUP BY name, period
    ORDER BY total_points DESC
    """
    return pd.read_sql_query(query, conn)