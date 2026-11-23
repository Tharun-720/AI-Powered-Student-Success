"""
Database management module for TREKVERSE AI-Powered Student Success Platform.
Provides SQLite database connection, transaction handling, role authentication, and CRUD services.
"""

import os
import sqlite3
import hashlib
import secrets
import json
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "student_success.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Return a database connection with Row factory enabled."""
    path = db_path or DEFAULT_DB_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path, timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path: Optional[str] = None):
    """Initialize database tables using schema.sql and populate default settings."""
    conn = get_db_connection(db_path)
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    
    # Insert default settings if not present
    default_settings = [
        ("high_risk_threshold_attendance", "75.0", "Attendance below this % contributes to High Risk"),
        ("high_risk_threshold_cgpa", "6.0", "CGPA below this contributes to High Risk"),
        ("moderate_risk_threshold_attendance", "80.0", "Attendance below this % contributes to Moderate Risk"),
        ("model_active_version", "v1.0.0-ensemble", "Active model version tag for scoring"),
        ("max_score_scale", "20.0", "Display scale for predicted final scores (e.g. 20.0 or 100.0)"),
        ("institution_name", "TREKVERSE AI ACADEMY", "Official academic institution label")
    ]
    for key, val, desc in default_settings:
        conn.execute(
            "INSERT OR IGNORE INTO system_settings (key, value, description) VALUES (?, ?, ?)",
            (key, val, desc)
        )
    conn.commit()
    conn.close()

# Password Security (Standard Library PBKDF2)
def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
    ).hex()
    return hashed, salt

def verify_password(password: str, hashed: str, salt: str) -> bool:
    new_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(new_hash, hashed)

# Authentication & User Management
def authenticate_user(username: str, password: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND status = 'active'", (username,))
    row = cursor.fetchone()
    conn.close()
    if row and verify_password(password, row["password_hash"], row["salt"]):
        return dict(row)
    return None

def create_user(
    username: str,
    password: str,
    role: str,
    full_name: str,
    email: str,
    department: str,
    db_path: Optional[str] = None
) -> int:
    hashed, salt = hash_password(password)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO users (username, password_hash, salt, role, full_name, email, department)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (username, hashed, salt, role, full_name, email, department)
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id

def list_users(role: Optional[str] = None, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    if role:
        cursor.execute("SELECT id, username, role, full_name, email, department, status, created_at FROM users WHERE role = ?", (role,))
    else:
        cursor.execute("SELECT id, username, role, full_name, email, department, status, created_at FROM users ORDER BY role, full_name")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Student Queries
def list_students(
    department: Optional[str] = None,
    semester: Optional[int] = None,
    risk_band: Optional[str] = None,
    search_query: Optional[str] = None,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    query = """
        SELECT s.*, 
               p.predicted_score, p.predicted_scale, p.risk_band, p.risk_score, p.model_version
        FROM students s
        LEFT JOIN (
            SELECT p1.*
            FROM predictions p1
            INNER JOIN (
                SELECT student_id, MAX(created_at) as max_created
                FROM predictions
                GROUP BY student_id
            ) p2 ON p1.student_id = p2.student_id AND p1.created_at = p2.max_created
        ) p ON s.student_id = p.student_id
        WHERE 1=1
    """
    params = []
    if department and department != "All":
        query += " AND s.department = ?"
        params.append(department)
    if semester and semester != 0:
        query += " AND s.semester = ?"
        params.append(semester)
    if risk_band and risk_band != "All":
        query += " AND p.risk_band = ?"
        params.append(risk_band)
    if search_query:
        query += " AND (s.student_id LIKE ? OR s.name LIKE ?)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])
        
    query += " ORDER BY s.student_id ASC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_student(student_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_student_by_user_id(user_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def upsert_student(data: Dict[str, Any], db_path: Optional[str] = None):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO students (
            student_id, user_id, name, department, semester, cgpa, attendance, 
            attendance_trend, backlogs, study_hours, assignment_completion, activity_score
        ) VALUES (
            :student_id, :user_id, :name, :department, :semester, :cgpa, :attendance, 
            :attendance_trend, :backlogs, :study_hours, :assignment_completion, :activity_score
        ) ON CONFLICT(student_id) DO UPDATE SET
            name = excluded.name,
            department = excluded.department,
            semester = excluded.semester,
            cgpa = excluded.cgpa,
            attendance = excluded.attendance,
            attendance_trend = excluded.attendance_trend,
            backlogs = excluded.backlogs,
            study_hours = excluded.study_hours,
            assignment_completion = excluded.assignment_completion,
            activity_score = excluded.activity_score
        """,
        {
            "student_id": data["student_id"],
            "user_id": data.get("user_id"),
            "name": data["name"],
            "department": data["department"],
            "semester": int(data["semester"]),
            "cgpa": float(data["cgpa"]),
            "attendance": float(data["attendance"]),
            "attendance_trend": float(data.get("attendance_trend", 0.0)),
            "backlogs": int(data.get("backlogs", 0)),
            "study_hours": float(data.get("study_hours", 2.0)),
            "assignment_completion": float(data.get("assignment_completion", 80.0)),
            "activity_score": float(data.get("activity_score", 70.0))
        }
    )
    conn.commit()
    conn.close()

# Marks & Subjects
def get_student_marks(student_id: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT m.id, m.student_id, s.name as subject_name, s.code as subject_code,
               m.exam_type, m.score, m.max_score, m.recorded_at
        FROM marks m
        JOIN subjects s ON m.subject_id = s.id
        WHERE m.student_id = ?
        ORDER BY s.name, m.exam_type
        """,
        (student_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_subjects_catalog(department: Optional[str] = None, semester: Optional[int] = None, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    query = "SELECT * FROM subjects WHERE 1=1"
    params = []
    if department and department != "All":
        query += " AND department = ?"
        params.append(department)
    if semester and semester != 0:
        query += " AND semester = ?"
        params.append(semester)
    query += " ORDER BY code ASC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Predictions
def save_prediction(
    student_id: str,
    model_version: str,
    predicted_score: float,
    predicted_scale: float,
    risk_band: str,
    risk_score: float,
    explanation: Dict[str, Any],
    db_path: Optional[str] = None
) -> int:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO predictions (
            student_id, model_version, predicted_score, predicted_scale,
            risk_band, risk_score, explanation_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            student_id, model_version, round(predicted_score, 2), predicted_scale,
            risk_band, round(risk_score, 3), json.dumps(explanation)
        )
    )
    pred_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return pred_id

def get_latest_prediction(student_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM predictions 
        WHERE student_id = ? 
        ORDER BY created_at DESC 
        LIMIT 1
        """,
        (student_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    res = dict(row)
    if res.get("explanation_json"):
        try:
            res["explanation"] = json.loads(res["explanation_json"])
        except Exception:
            res["explanation"] = {}
    return res

# Interventions
def list_interventions(
    faculty_id: Optional[int] = None,
    status: Optional[str] = None,
    student_id: Optional[str] = None,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    query = """
        SELECT i.*, s.name as student_name, s.department, s.semester, u.full_name as faculty_name
        FROM interventions i
        JOIN students s ON i.student_id = s.student_id
        JOIN users u ON i.faculty_id = u.id
        WHERE 1=1
    """
    params = []
    if faculty_id:
        query += " AND i.faculty_id = ?"
        params.append(faculty_id)
    if status and status != "All":
        query += " AND i.status = ?"
        params.append(status)
    if student_id:
        query += " AND i.student_id = ?"
        params.append(student_id)
    query += " ORDER BY i.created_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_intervention(
    student_id: str,
    faculty_id: int,
    issue_summary: str,
    action_plan: str,
    notes: Optional[str] = "",
    status: str = "Open",
    db_path: Optional[str] = None
) -> int:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO interventions (student_id, faculty_id, issue_summary, action_plan, notes, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (student_id, faculty_id, issue_summary, action_plan, notes, status)
    )
    iid = cursor.lastrowid
    conn.commit()
    conn.close()
    return iid

def update_intervention(
    intervention_id: int,
    status: str,
    notes: Optional[str] = None,
    db_path: Optional[str] = None
):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    if notes is not None:
        cursor.execute(
            """
            UPDATE interventions 
            SET status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
            """,
            (status, notes, intervention_id)
        )
    else:
        cursor.execute(
            """
            UPDATE interventions 
            SET status = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
            """,
            (status, intervention_id)
        )
    conn.commit()
    conn.close()

# Recommendations & Study Plans
def get_student_recommendations(student_id: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM recommendations WHERE student_id = ? ORDER BY priority DESC, created_at DESC",
        (student_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_recommendation(
    student_id: str,
    recommendation_text: str,
    category: str,
    priority: str,
    subject: Optional[str] = None,
    db_path: Optional[str] = None
):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO recommendations (student_id, subject, recommendation_text, category, priority)
        VALUES (?, ?, ?, ?, ?)
        """,
        (student_id, subject, recommendation_text, category, priority)
    )
    conn.commit()
    conn.close()

def get_study_plans(student_id: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM study_plans WHERE student_id = ? ORDER BY id ASC",
        (student_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_study_plan_task(
    student_id: str,
    day_of_week: str,
    subject: str,
    activity: str,
    duration_hours: float,
    time_slot: str = "Evening",
    db_path: Optional[str] = None
) -> int:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO study_plans (student_id, day_of_week, time_slot, subject, activity, duration_hours, completed)
        VALUES (?, ?, ?, ?, ?, ?, 0)
        """,
        (student_id, day_of_week, time_slot, subject, activity, duration_hours)
    )
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return task_id

def toggle_study_task(task_id: int, completed: bool, db_path: Optional[str] = None):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE study_plans SET completed = ? WHERE id = ?", (1 if completed else 0, task_id))
    conn.commit()
    conn.close()

def clear_study_plan(student_id: str, db_path: Optional[str] = None):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM study_plans WHERE student_id = ?", (student_id,))
    conn.commit()
    conn.close()

# System Settings & Audit Logs
def get_setting(key: str, default: str = "", db_path: Optional[str] = None) -> str:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM system_settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else default

def set_setting(key: str, value: str, description: Optional[str] = None, db_path: Optional[str] = None):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO system_settings (key, value, description, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
        """,
        (key, value, description)
    )
    conn.commit()
    conn.close()

def log_audit(user_id: Optional[int], action: str, details: str, db_path: Optional[str] = None):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO audit_logs (user_id, action, details) VALUES (?, ?, ?)",
        (user_id, action, details)
    )
    conn.commit()
    conn.close()

def get_recent_audit_logs(limit: int = 50, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT a.*, u.username, u.role
        FROM audit_logs a
        LEFT JOIN users u ON a.user_id = u.id
        ORDER BY a.timestamp DESC
        LIMIT ?
        """,
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Overview Analytics
def get_dashboard_summary(db_path: Optional[str] = None) -> Dict[str, Any]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total_students, AVG(cgpa) as avg_cgpa, AVG(attendance) as avg_attendance FROM students")
    base_stats = dict(cursor.fetchone() or {"total_students": 0, "avg_cgpa": 0.0, "avg_attendance": 0.0})
    
    cursor.execute("""
        SELECT 
            p.risk_band, COUNT(*) as count
        FROM (
            SELECT p1.student_id, p1.risk_band
            FROM predictions p1
            INNER JOIN (
                SELECT student_id, MAX(created_at) as max_c
                FROM predictions
                GROUP BY student_id
            ) p2 ON p1.student_id = p2.student_id AND p1.created_at = p2.max_c
        ) p
        GROUP BY p.risk_band
    """)
    risk_counts = {r["risk_band"]: r["count"] for r in cursor.fetchall()}
    
    cursor.execute("SELECT COUNT(*) as open_interventions FROM interventions WHERE status != 'Resolved'")
    open_interventions = cursor.fetchone()["open_interventions"]
    
    conn.close()
    return {
        "total_students": base_stats["total_students"] or 0,
        "avg_cgpa": round(base_stats["avg_cgpa"] or 0.0, 2),
        "avg_attendance": round(base_stats["avg_attendance"] or 0.0, 1),
        "low_risk": risk_counts.get("Low Risk", 0),
        "moderate_risk": risk_counts.get("Moderate Risk", 0),
        "high_risk": risk_counts.get("High Risk", 0),
        "requiring_support": risk_counts.get("High Risk", 0) + risk_counts.get("Moderate Risk", 0),
        "open_interventions": open_interventions
    }

