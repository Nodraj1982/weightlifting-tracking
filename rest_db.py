import sqlite3

DB_FILE = "lifting.db"

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

# Drop old tables if they exist
cur.executescript("""
DROP TABLE IF EXISTS WorkoutEntries;
DROP TABLE IF EXISTS Workouts;
DROP TABLE IF EXISTS ExerciseProgress;
DROP TABLE IF EXISTS Exercises;
""")

# Recreate tables with fresh schema
cur.executescript("""
CREATE TABLE Exercises (
    ExerciseID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT NOT NULL UNIQUE COLLATE NOCASE,
    Category TEXT,
    Equipment TEXT
);

CREATE TABLE ExerciseProgress (
    ExerciseID INTEGER PRIMARY KEY,
    CurrentScheme INTEGER,
    CurrentWeight REAL,
    LastResult TEXT,
    LastUpdated DATE,
    FOREIGN KEY (ExerciseID) REFERENCES Exercises (ExerciseID)
);

CREATE TABLE Workouts (
    WorkoutID INTEGER PRIMARY KEY AUTOINCREMENT,
    WorkoutDate DATE,
    Notes TEXT
);

CREATE TABLE WorkoutEntries (
    EntryID INTEGER PRIMARY KEY AUTOINCREMENT,
    WorkoutID INTEGER,
    ExerciseID INTEGER,
    Sets INTEGER,
    Reps INTEGER,
    Weight REAL,
    FOREIGN KEY (WorkoutID) REFERENCES Workouts (WorkoutID),
    FOREIGN KEY (ExerciseID) REFERENCES Exercises (ExerciseID)
);
""")

conn.commit()
conn.close()

print("✅ Database reset complete. Fresh schema created.")