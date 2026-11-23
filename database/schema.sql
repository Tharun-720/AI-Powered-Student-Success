-- TREKVERSE AI-Powered Student Success Prediction & Academic Guidance System
-- Database Schema (SQLite compatible)

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'faculty', 'student')),
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    department TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'suspended', 'inactive')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    semester INTEGER NOT NULL,
    credits INTEGER DEFAULT 3
);

CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    user_id INTEGER,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    semester INTEGER NOT NULL,
    cgpa REAL NOT NULL CHECK(cgpa >= 0.0 AND cgpa <= 10.0),
    attendance REAL NOT NULL CHECK(attendance >= 0.0 AND attendance <= 100.0),
    attendance_trend REAL DEFAULT 0.0, -- change over last month in %
    backlogs INTEGER NOT NULL DEFAULT 0 CHECK(backlogs >= 0),
    study_hours REAL NOT NULL DEFAULT 2.0 CHECK(study_hours >= 0.0),
    assignment_completion REAL NOT NULL DEFAULT 80.0 CHECK(assignment_completion >= 0.0 AND assignment_completion <= 100.0),
    activity_score REAL NOT NULL DEFAULT 70.0 CHECK(activity_score >= 0.0 AND activity_score <= 100.0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    subject_id INTEGER NOT NULL,
    date DATE NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('Present', 'Absent', 'Excused')),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS marks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    subject_id INTEGER NOT NULL,
    exam_type TEXT NOT NULL CHECK(exam_type IN ('Quiz', 'Midterm', 'Assignment', 'Internal', 'Final')),
    score REAL NOT NULL,
    max_score REAL NOT NULL DEFAULT 100.0,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    subject_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    score REAL,
    max_score REAL DEFAULT 100.0,
    status TEXT NOT NULL CHECK(status IN ('Submitted', 'Pending', 'Late', 'Graded')),
    submission_date DATE,
    FOREIGN KEY(student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    model_version TEXT NOT NULL,
    predicted_score REAL NOT NULL,
    predicted_scale REAL DEFAULT 20.0,
    risk_band TEXT NOT NULL CHECK(risk_band IN ('Low Risk', 'Moderate Risk', 'High Risk')),
    risk_score REAL NOT NULL, -- Probability or composite risk metric (0.0 to 1.0)
    explanation_json TEXT, -- Serialized top positive/negative factors
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(student_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    subject TEXT,
    recommendation_text TEXT NOT NULL,
    category TEXT NOT NULL CHECK(category IN ('Study Habit', 'Topic Revision', 'Faculty Meeting', 'Attendance Improvement', 'Assignment Submission')),
    priority TEXT NOT NULL CHECK(priority IN ('High', 'Medium', 'Low')),
    status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN ('Active', 'In Progress', 'Completed', 'Dismissed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(student_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS interventions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    faculty_id INTEGER NOT NULL,
    issue_summary TEXT NOT NULL,
    action_plan TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Open' CHECK(status IN ('Open', 'In Progress', 'Resolved')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY(faculty_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS study_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    day_of_week TEXT NOT NULL CHECK(day_of_week IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')),
    time_slot TEXT,
    subject TEXT NOT NULL,
    activity TEXT NOT NULL,
    duration_hours REAL NOT NULL,
    completed INTEGER DEFAULT 0 CHECK(completed IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(student_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS system_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    details TEXT,
    ip_address TEXT DEFAULT '127.0.0.1',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Indices for performance
CREATE INDEX IF NOT EXISTS idx_students_dept_sem ON students(department, semester);
CREATE INDEX IF NOT EXISTS idx_predictions_student ON predictions(student_id);
CREATE INDEX IF NOT EXISTS idx_marks_student ON marks(student_id);
CREATE INDEX IF NOT EXISTS idx_interventions_student ON interventions(student_id);

