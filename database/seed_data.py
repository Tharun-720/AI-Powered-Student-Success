"""
Database Seeding Script for TREKVERSE Student Success Platform.
Populates standard departments, course catalog, role-based accounts (Admin, Faculty, Student),
296 realistic student benchmark records, subject marks, initial predictions, and sample interventions.
"""

import os
import sys
import pandas as pd
import numpy as np

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database.database import (
    init_db, get_db_connection, create_user, upsert_student,
    save_prediction, create_intervention, save_recommendation, save_study_plan_task,
    set_setting, log_audit
)
from src.training.model_trainer import (
    train_and_evaluate_models, generate_benchmark_dataset, DATA_RAW_DIR
)
from src.clustering.student_segmentation import train_student_clustering
from src.prediction.predictor import StudentPredictor
from src.recommendations.recommender import generate_personalized_recommendations, build_weekly_study_schedule

def seed_database():
    print("1. Initializing database schema...")
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    print("2. Seeding departments and subjects...")
    departments = [
        ("CS", "Computer Science"),
        ("IT", "Information Technology"),
        ("ECE", "Electronics & Communication"),
        ("DSAI", "Data Science & AI")
    ]
    for code, name in departments:
        cursor.execute("INSERT OR IGNORE INTO departments (code, name) VALUES (?, ?)", (code, name))

    subjects = [
        ("CS301", "Mathematics", "Computer Science", 5, 4),
        ("CS302", "Programming", "Computer Science", 5, 4),
        ("CS303", "DBMS", "Computer Science", 5, 3),
        ("CS304", "Computer Networks", "Computer Science", 5, 3),
        ("EC305", "Electronics", "Computer Science", 5, 3),
        ("IT301", "Web Engineering", "Information Technology", 5, 3),
        ("DS301", "Machine Learning Core", "Data Science", 5, 4)
    ]
    for code, name, dept, sem, creds in subjects:
        cursor.execute(
            "INSERT OR IGNORE INTO subjects (code, name, department, semester, credits) VALUES (?, ?, ?, ?, ?)",
            (code, name, dept, sem, creds)
        )
    conn.commit()

    print("3. Creating default role-based user accounts...")
    # Admin
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        create_user("admin", "admin123", "admin", "Institutional Administrator", "admin@trekverse.edu", "Administration")

    # Faculty members
    cursor.execute("SELECT id FROM users WHERE username = 'prof_sharma'")
    if not cursor.fetchone():
        create_user("prof_sharma", "faculty123", "faculty", "Prof. R. Sharma (HOD CS)", "r.sharma@trekverse.edu", "Computer Science")

    cursor.execute("SELECT id FROM users WHERE username = 'prof_rao'")
    if not cursor.fetchone():
        create_user("prof_rao", "faculty123", "faculty", "Dr. Anita Rao", "a.rao@trekverse.edu", "Data Science")

    # Student accounts for testing
    cursor.execute("SELECT id FROM users WHERE username = 'stu1024'")
    stu1024_uid = None
    if not cursor.fetchone():
        stu1024_uid = create_user("stu1024", "student123", "student", "Kavya Deshmukh", "stu1024@trekverse.edu", "Computer Science")
    else:
        cursor.execute("SELECT id FROM users WHERE username = 'stu1024'")
        stu1024_uid = cursor.fetchone()["id"]

    cursor.execute("SELECT id FROM users WHERE username = 'stu1000'")
    stu1000_uid = None
    if not cursor.fetchone():
        stu1000_uid = create_user("stu1000", "student123", "student", "Aarav Sharma", "stu1000@trekverse.edu", "Computer Science")
    else:
        cursor.execute("SELECT id FROM users WHERE username = 'stu1000'")
        stu1000_uid = cursor.fetchone()["id"]

    cursor.execute("SELECT id FROM users WHERE username = 'stu1050'")
    stu1050_uid = None
    if not cursor.fetchone():
        stu1050_uid = create_user("stu1050", "student123", "student", "Devansh Joshi", "stu1050@trekverse.edu", "Electronics")
    else:
        cursor.execute("SELECT id FROM users WHERE username = 'stu1050'")
        stu1050_uid = cursor.fetchone()["id"]

    print("4. Training ML models and student clustering...")
    metadata = train_and_evaluate_models()
    
    raw_csv = os.path.join(DATA_RAW_DIR, "student_academic_records.csv")
    df = pd.read_csv(raw_csv)
    
    # Run clustering
    train_student_clustering(df, n_clusters=4, seed=42)

    # 5. Populate Students into Database
    print(f"5. Seeding {len(df)} student profiles into database...")
    for idx, row in df.iterrows():
        sid = row["student_id"]
        uid = None
        if sid == "STU1024":
            uid = stu1024_uid
            # Calibrate STU1024 to exactly reflect PDF Page 4 illustrative example!
            # Attendance: 68%, previous failures: 1, predicted score: ~13.6/20, Risk: Moderate
            row["attendance"] = 68.0
            row["backlogs"] = 1
            row["previous_cgpa"] = 6.9
            row["study_hours"] = 2.0
            row["assignment_completion"] = 65.0
            row["activity_score"] = 60.0
            row["name"] = "Kavya Deshmukh"
        elif sid == "STU1000":
            uid = stu1000_uid
            row["name"] = "Aarav Sharma"
            row["attendance"] = 94.0
            row["previous_cgpa"] = 8.9
            row["backlogs"] = 0
        elif sid == "STU1050":
            uid = stu1050_uid
            row["name"] = "Devansh Joshi"
            row["attendance"] = 58.0
            row["backlogs"] = 2
            row["previous_cgpa"] = 5.2

        upsert_student({
            "student_id": sid,
            "user_id": uid,
            "name": row["name"],
            "department": row["department"],
            "semester": int(row["semester"]),
            "cgpa": float(row["previous_cgpa"]),
            "attendance": float(row["attendance"]),
            "attendance_trend": float(row.get("attendance_trend", 0.0)),
            "backlogs": int(row.get("backlogs", 0)),
            "study_hours": float(row.get("study_hours", 2.0)),
            "assignment_completion": float(row.get("assignment_marks", 80.0)),
            "activity_score": float(row.get("activity_score", 70.0))
        })

    # 6. Populate Marks and Subject records for sample students
    print("6. Seeding subject marks for curriculum evaluation...")
    cursor.execute("SELECT id, name FROM subjects WHERE department = 'Computer Science'")
    cs_subjs = cursor.fetchall()
    
    for sid in ["STU1000", "STU1024", "STU1050"]:
        for subj in cs_subjs:
            s_id = subj["id"]
            s_name = subj["name"]
            if sid == "STU1000":
                score = np.random.uniform(80, 95)
            elif sid == "STU1024":
                score = 58.0 if s_name == "DBMS" or s_name == "Mathematics" else np.random.uniform(65, 78)
            else:
                score = np.random.uniform(42, 60)

            cursor.execute(
                "INSERT INTO marks (student_id, subject_id, exam_type, score, max_score) VALUES (?, ?, ?, ?, ?)",
                (sid, s_id, "Midterm", round(score, 1), 100.0)
            )
            cursor.execute(
                "INSERT INTO marks (student_id, subject_id, exam_type, score, max_score) VALUES (?, ?, ?, ?, ?)",
                (sid, s_id, "Assignment", round(score + np.random.uniform(-4, 5), 1), 100.0)
            )
    conn.commit()

    # 7. Generate Live Predictions and Recommendations for all students
    print("7. Running prediction engine and generating explainable insights...")
    predictor = StudentPredictor()

    for idx, row in df.iterrows():
        sid = row["student_id"]
        res = predictor.predict_student(dict(row), scale=20.0)
        save_prediction(
            student_id=sid,
            model_version=res["model_version"],
            predicted_score=res["predicted_score"],
            predicted_scale=res["predicted_scale"],
            risk_band=res["risk_band"],
            risk_score=res["risk_score"],
            explanation=res["explanation"]
        )

        # Generate sample recommendations for moderate & high risk students
        if res["risk_band"] in ["High Risk", "Moderate Risk"]:
            subj_preds = predictor.predict_subject_wise(dict(row), scale=20.0)
            recs = generate_personalized_recommendations(dict(row), subj_preds)
            for r in recs[:2]:
                save_recommendation(
                    student_id=sid,
                    recommendation_text=r["text"],
                    category=r["category"],
                    priority=r["priority"],
                    subject=r.get("subject")
                )

    # 8. Create sample faculty interventions (Section 5 & 10)
    print("8. Seeding faculty interventions and study plans...")
    cursor.execute("SELECT id FROM users WHERE username = 'prof_sharma'")
    prof_id = cursor.fetchone()["id"]

    create_intervention(
        student_id="STU1024",
        faculty_id=prof_id,
        issue_summary="Attendance dipped to 68% and struggling in DBMS & Mathematics concepts.",
        action_plan="1) Assigned weekly DBMS revision tasks; 2) Scheduled bi-weekly attendance audit with academic advisor.",
        notes="Student acknowledged commute challenges. Agreed on 1.5 hr/day focused study plan.",
        status="In Progress"
    )

    create_intervention(
        student_id="STU1050",
        faculty_id=prof_id,
        issue_summary="High Risk Flag: Attendance at 58% with 2 active backlogs in previous semesters.",
        action_plan="Urgent advisory consultation with parents & remedial tutoring enrollment.",
        notes="Counseling notice issued; waiting for confirmation from department dean.",
        status="Open"
    )

    # Create personalized study plan for STU1024
    stu1024_tasks = build_weekly_study_schedule(
        {"student_id": "STU1024", "attendance": 68.0, "study_hours": 2.0},
        weak_subjects=["DBMS", "Mathematics", "Electronics"]
    )
    for task in stu1024_tasks:
        save_study_plan_task(
            student_id="STU1024",
            day_of_week=task["day_of_week"],
            subject=task["subject"],
            activity=task["activity"],
            duration_hours=task["duration_hours"],
            time_slot=task["time_slot"]
        )

    log_audit(prof_id, "SYSTEM_SEED", "Initial institutional benchmark dataset and student profiles seeded successfully.")
    conn.commit()
    conn.close()
    print("Seeding completed successfully!")

if __name__ == "__main__":
    seed_database()

