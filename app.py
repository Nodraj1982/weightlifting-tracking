import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

DB_FILE = "lifting.db"

# ---------------------------
# Database helpers
# ---------------------------
def get_connection():
    return sqlite3.connect(DB_FILE)

def add_exercise(name, category, equipment, starting_weight):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO Exercises (Name, Category, Equipment) VALUES (?, ?, ?)",
                (name, category, equipment))
    exercise_id = cur.lastrowid
    cur.execute("""INSERT INTO ExerciseProgress 
                   (ExerciseID, CurrentScheme, CurrentWeight, LastResult, LastUpdated) 
                   VALUES (?, ?, ?, ?, ?)""",
                (exercise_id, 15, starting_weight, 'Success', date.today()))
    conn.commit()
    conn.close()

def get_exercises():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT ExerciseID, Name FROM Exercises ORDER BY Name")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_dashboard_data():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT e.Name,
               p.CurrentScheme,
               p.CurrentWeight,
               p.LastResult,
               p.LastUpdated
        FROM ExerciseProgress p
        JOIN Exercises e ON e.ExerciseID = p.ExerciseID
        ORDER BY p.LastUpdated DESC
    """)
    rows = cur.fetchall()
    conn.close()
    cleaned_rows = []
    for name, scheme, weight, result, updated in rows:
        display_weight = "Increase weight" if weight is None else weight
        cleaned_rows.append((name, scheme, display_weight, result, updated))
    return pd.DataFrame(cleaned_rows, columns=["Exercise", "Scheme (reps)", "Weight (kg)", "Last Result", "Last Performed"])

def get_workout_history():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT w.WorkoutDate,
               e.Name,
               we.Sets,
               we.Reps,
               we.Weight,
               we.Result,
               w.Notes
        FROM WorkoutEntries we
        JOIN Workouts w ON we.WorkoutID = w.WorkoutID
        JOIN Exercises e ON we.ExerciseID = e.ExerciseID
        ORDER BY w.WorkoutDate DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return pd.DataFrame(rows, columns=["Date", "Exercise", "Sets", "Reps", "Weight (kg)", "Result", "Notes"])

def get_next_progression(current_scheme, current_weight, result):
    if result == "Success":
        return current_scheme, None
    else:
        if current_scheme == 15:
            return 10, current_weight
        elif current_scheme == 10:
            return 5, current_weight
        else:
            return 15, current_weight

# ---------------------------
# Navigation
# ---------------------------
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Add Exercises", "Workout History", "Next Workout"])

# ---------------------------
# Page 1: Add Exercises
# ---------------------------
if page == "Add Exercises":
    st.title("🏋️ Add Exercises")
    duplicate_name = None

    st.header("➕ Add a New Exercise")
    with st.form("add_exercise_form"):
        name = st.text_input("Exercise Name")
        category = st.text_input("Category (optional)")
        equipment = st.text_input("Equipment (optional)")
        starting_weight = st.number_input("Starting Weight (kg)", min_value=0.0, step=2.5)
        submitted = st.form_submit_button("Add Exercise")

        if submitted and name.strip():
            try:
                add_exercise(name.strip(), category.strip(), equipment.strip(), starting_weight)
                st.success(f"Exercise '{name}' added successfully!")
            except sqlite3.IntegrityError:
                duplicate_name = name.strip()
                st.error(f"❌ The exercise '{duplicate_name}' already exists (case‑insensitive).")

    st.header("📋 Current Exercises")
    exercises = get_exercises()
    if exercises:
        for ex in exercises:
            st.write(f"- {ex[1]} (ID: {ex[0]})")
    else:
        st.info("No exercises added yet. Use the form above to add one.")


# ---------------------------
# Page 2: Workout History
# ---------------------------
elif page == "Workout History":
    st.title("📜 Workout History")

    df = get_workout_history()

    if not df.empty:
        # Ensure Date column is datetime
        df["Date"] = pd.to_datetime(df["Date"])

        # --- Date range filter ---
        default_start = df["Date"].min().date()
        default_end = df["Date"].max().date()
        start_date, end_date = st.date_input(
            "Select date range",
            value=(default_start, default_end)
        )

        # --- Exercise filter ---
        exercises = ["All"] + sorted(df["Exercise"].unique().tolist())
        selected_exercise = st.selectbox("Filter by exercise", exercises)

        # Apply filters
        mask = (df["Date"].dt.date >= start_date) & (df["Date"].dt.date <= end_date)
        filtered_df = df.loc[mask]

        if selected_exercise != "All":
            filtered_df = filtered_df[filtered_df["Exercise"] == selected_exercise]

        # Show results
        if not filtered_df.empty:
            st.dataframe(filtered_df, use_container_width=True)
        else:
            st.warning("No workouts found for this selection.")
    else:
        st.info("No workouts logged yet.")

# ---------------------------
# Page 3: Next Workout
# ---------------------------
elif page == "Next Workout":
    st.title("🎯 Next Workout Plan")

    exercises = get_exercises()
    if exercises:
        # --- Log Workout Attempt ---
        st.header("📝 Log a Workout Attempt")
        exercise_names = {ex[1]: ex[0] for ex in exercises}
        selected_exercise = st.selectbox("Choose Exercise", list(exercise_names.keys()))
        sets = st.number_input("Sets", min_value=1, value=3)
        reps = st.number_input("Reps", min_value=1, value=15)
        weight = st.number_input("Weight (kg)", min_value=0.0, step=2.5)
        result = st.radio("Result", ["Success", "Fail"])
        notes = st.text_area("Notes (optional)")
        workout_date = st.date_input("Workout Date", value=date.today())

        if st.button("Save Workout"):
            conn = get_connection()
            cur = conn.cursor()

            # Insert workout + entry
            cur.execute("INSERT INTO Workouts (WorkoutDate, Notes) VALUES (?, ?)",
                        (workout_date, notes))
            workout_id = cur.lastrowid
            cur.execute("""INSERT INTO WorkoutEntries 
                           (WorkoutID, ExerciseID, Sets, Reps, Weight, Result) 
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (workout_id, exercise_names[selected_exercise], sets, reps, weight, result))

            # Get current scheme/weight
            cur.execute("SELECT CurrentScheme, CurrentWeight FROM ExerciseProgress WHERE ExerciseID = ?",
                        (exercise_names[selected_exercise],))
            current_scheme, current_weight = cur.fetchone()

            # Apply progression rules
            next_scheme, next_weight = get_next_progression(current_scheme, weight, result)

            # Update ExerciseProgress
            cur.execute("""UPDATE ExerciseProgress
                           SET CurrentScheme = ?,
                               CurrentWeight = ?,
                               LastResult = ?,
                               LastUpdated = ?
                           WHERE ExerciseID = ?""",
                        (next_scheme, next_weight if next_weight is not None else weight,
                         result, workout_date, exercise_names[selected_exercise]))

            conn.commit()
            conn.close()

            st.success(f"Workout for {selected_exercise} logged successfully!")
            if next_weight is None:
                st.info(f"Next target for {selected_exercise}: {next_scheme} reps — increase weight")
            else:
                st.info(f"Next target for {selected_exercise}: {next_scheme} reps at {next_weight} kg")

        # --- Dashboard / Plan ---
        st.header("📊 Current Plan")
        df = get_dashboard_data()
        if not df.empty:
            for _, row in df.iterrows():
                if row["Weight (kg)"] == "Increase weight":
                    st.write(f"**{row['Exercise']}** → {row['Scheme (reps)']} reps — increase weight")
                else:
                    st.write(f"**{row['Exercise']}** → {row['Scheme (reps)']} reps at {row['Weight (kg)']} kg")
        else:
            st.info("No workouts logged yet. Once you log, your plan will appear here.")
    else:
        st.info("No exercises available. Add one first on the 'Add Exercises' page.")