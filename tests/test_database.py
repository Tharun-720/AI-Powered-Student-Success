"""
Unit tests for database module, authentication, and CRUD transactions.
"""

import pytest
import os
import sqlite3
import tempfile
from database.database import (
    init_db, get_db_connection, create_user, authenticate_user,
    upsert_student, get_student, list_students, save_prediction,
    get_latest_prediction, create_intervention, update_intervention,
    list_interventions, save_study_plan_task, toggle_study_task,
    get_study_plans
)

@pytest.fixture
def temp_db():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    init_db(db_path)
    yield db_path
    if os.path.exists(db_path):
        os.remove(db_path)

def test_user_authentication_and_hashing(temp_db):
    uid = create_user("testadmin", "Secret123!", "admin", "Test Admin", "admin@test.edu", "AdminDept", db_path=temp_db)
    assert uid > 0

    # Valid login
    user = authenticate_user("testadmin", "Secret123!", db_path=temp_db)
    assert user is not None
    assert user["username"] == "testadmin"
    assert user["role"] == "admin"

    # Invalid login
    bad_user = authenticate_user("testadmin", "WrongPass", db_path=temp_db)
    assert bad_user is None

    non_user = authenticate_user("nonexistent", "Secret123!", db_path=temp_db)
    assert non_user is None

def test_student_upsert_and_retrieval(temp_db):
    data = {
        "student_id": "TEST_STU101",
        "name": "Alex Mercer",
        "department": "Computer Science",
        "semester": 5,
        "cgpa": 8.4,
        "attendance": 88.5,
        "backlogs": 0,
        "study_hours": 3.5,
        "assignment_completion": 90.0,
        "activity_score": 85.0
    }
    upsert_student(data, db_path=temp_db)
    stu = get_student("TEST_STU101", db_path=temp_db)
    assert stu is not None
    assert stu["name"] == "Alex Mercer"
    assert stu["cgpa"] == 8.4
    assert stu["attendance"] == 88.5

def test_predictions_persistence(temp_db):
    test_stu = {
        "student_id": "TEST_STU102",
        "name": "Bruce Wayne",
        "department": "Information Technology",
        "semester": 4,
        "cgpa": 7.2,
        "attendance": 78.0
    }
    upsert_student(test_stu, db_path=temp_db)

    pid = save_prediction(
        student_id="TEST_STU102",
        model_version="v1.0.0-test",
        predicted_score=14.5,
        predicted_scale=20.0,
        risk_band="Moderate Risk",
        risk_score=0.45,
        explanation={"top_positive": [], "top_negative": []},
        db_path=temp_db
    )
    assert pid > 0

    pred = get_latest_prediction("TEST_STU102", db_path=temp_db)
    assert pred is not None
    assert pred["predicted_score"] == 14.5
    assert pred["risk_band"] == "Moderate Risk"

def test_interventions_workflow(temp_db):
    fac_id = create_user("faculty1", "pass123", "faculty", "Prof Davis", "davis@test.edu", "CS", db_path=temp_db)
    upsert_student({"student_id": "STU_INT", "name": "Peter Parker", "department": "CS", "semester": 5, "cgpa": 6.2, "attendance": 65.0}, db_path=temp_db)

    iid = create_intervention(
        student_id="STU_INT",
        faculty_id=fac_id,
        issue_summary="Attendance below threshold",
        action_plan="Schedule weekly review",
        notes="First check-in scheduled",
        status="Open",
        db_path=temp_db
    )
    assert iid > 0

    # Update status
    update_intervention(iid, status="In Progress", notes="Meeting conducted", db_path=temp_db)
    all_ints = list_interventions(student_id="STU_INT", db_path=temp_db)
    assert len(all_ints) == 1
    assert all_ints[0]["status"] == "In Progress"

def test_study_plan_tasks(temp_db):
    upsert_student({"student_id": "STU_PLAN", "name": "Diana Prince", "department": "CS", "semester": 5, "cgpa": 8.5, "attendance": 92.0}, db_path=temp_db)

    tid = save_study_plan_task("STU_PLAN", "Monday", "DBMS", "Read Chapter 4", 1.5, db_path=temp_db)
    assert tid > 0

    plans = get_study_plans("STU_PLAN", db_path=temp_db)
    assert len(plans) == 1
    assert plans[0]["completed"] == 0

    # Toggle task
    toggle_study_task(tid, True, db_path=temp_db)
    plans_updated = get_study_plans("STU_PLAN", db_path=temp_db)
    assert plans_updated[0]["completed"] == 1

