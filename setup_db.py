import sqlite3

# Connect (creates lifting.db if it doesn't exist)
conn = sqlite3.connect("lifting.db")
cur = conn.cursor()

# Create tables
cur.executescript("""
CREATE TABLE IF NOT EXISTS Exercises (
    ExerciseID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT NOT NULL UNIQUE,
    Category TEXT,
    Equipment TEXT
);

CREATE TABLE IF NOT EXISTS Workouts (
    WorkoutID INTEGER PRIMARY KEY AUTOINCREMENT,
    WorkoutDate DATE NOT NULL,
    Notes TEXT
);

CREATE TABLE IF NOT EXISTS WorkoutEntries (
    EntryID INTEGER PRIMARY KEY AUTOINCREMENT,
    WorkoutID INTEGER NOT NULL,
    ExerciseID INTEGER NOT NULL,
    Sets INTEGER NOT NULL,
    Reps INTEGER NOT NULL,
    Weight DECIMAL(5,2),
    FOREIGN KEY (WorkoutID) REFERENCES Workouts(WorkoutID),
    FOREIGN KEY (ExerciseID) REFERENCES Exercises(ExerciseID)
);

CREATE TABLE IF NOT EXISTS ExerciseProgress (
    ProgressID INTEGER PRIMARY KEY AUTOINCREMENT,
    ExerciseID INTEGER NOT NULL,
    CurrentScheme INTEGER NOT NULL CHECK(CurrentScheme IN (15, 10, 5)),
    CurrentWeight DECIMAL(5,2) NOT NULL,
    LastResult TEXT CHECK(LastResult IN ('Success', 'Fail')),
    LastUpdated DATE,
    FOREIGN KEY (ExerciseID) REFERENCES Exercises(ExerciseID)
);
""")

# No seeding here — user will add exercises via the app
conn.commit()
conn.close()
print("✅ Database initialised: lifting.db (empty, ready for user-defined exercises)")