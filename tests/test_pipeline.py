"""
Unit tests for data cleaning, feature engineering, prediction, what-if simulator, and clustering.
"""

import pytest
import pandas as pd
import numpy as np
from src.preprocessing.data_cleaner import validate_and_clean_data, auto_detect_column_mapping
from src.feature_engineering.feature_pipeline import engineer_features, calculate_heuristic_risk
from src.prediction.predictor import StudentPredictor
from src.clustering.student_segmentation import predict_student_cluster

def test_data_validation_integrity():
    # Valid dataframe
    raw_data = {
        "Roll No": ["STU9901", "STU9902"],
        "Student Name": ["John Doe", "Jane Roe"],
        "Attendance %": [85.0, 92.0],
        "CGPA": [7.8, 8.9],
        "Study Hours": [3.0, 4.0],
        "Backlogs": [0, 0]
    }
    df = pd.DataFrame(raw_data)
    mapping = auto_detect_column_mapping(list(df.columns))
    cleaned_df, errors, summary = validate_and_clean_data(df, mapping)
    assert summary["valid_rows"] == 2
    assert summary["rejected_rows"] == 0
    assert len(errors) == 0

    # Invalid dataframe with out-of-range attendance & negative study hours
    bad_data = {
        "student_id": ["STU9903", "STU9904"],
        "attendance": [150.0, -10.0],
        "previous_cgpa": [12.0, 7.5],
        "study_hours": [-2.0, 3.0]
    }
    bad_df = pd.DataFrame(bad_data)
    _, bad_errors, bad_summary = validate_and_clean_data(bad_df)
    assert bad_summary["rejected_rows"] == 2
    assert len(bad_errors) >= 3

def test_feature_engineering_pipeline():
    sample = pd.DataFrame([{
        "attendance": 68.0,
        "cgpa": 7.0,
        "internal_marks": 65.0,
        "assignment_marks": 70.0,
        "study_hours": 2.0,
        "backlogs": 1,
        "activity_score": 60.0
    }])
    feat_df = engineer_features(sample)
    assert "attendance_deficit" in feat_df.columns
    assert feat_df["attendance_deficit"].iloc[0] == 7.0 # 75 - 68 = 7
    assert "assessment_avg" in feat_df.columns
    assert feat_df["assessment_avg"].iloc[0] == 67.5 # (65 + 70)/2
    assert "engagement_index" in feat_df.columns
    assert 0.0 <= feat_df["engagement_index"].iloc[0] <= 1.0

def test_student_predictor_and_what_if():
    predictor = StudentPredictor()
    student = {
        "student_id": "TEST_SIM",
        "attendance": 70.0,
        "cgpa": 6.8,
        "internal_marks": 60.0,
        "assignment_marks": 65.0,
        "study_hours": 2.0,
        "backlogs": 1,
        "activity_score": 65.0
    }

    pred = predictor.predict_student(student, scale=20.0)
    assert "predicted_score" in pred
    assert 0.0 <= pred["predicted_score"] <= 20.0
    assert pred["risk_band"] in ["Low Risk", "Moderate Risk", "High Risk"]
    assert "explanation" in pred

    # Test What-If Simulator
    sim_inputs = {
        "attendance": 90.0,
        "study_hours": 4.0,
        "assignment_marks": 95.0
    }
    sim_result = predictor.simulate_what_if(student, sim_inputs, scale=20.0)
    assert "baseline" in sim_result
    assert "scenario" in sim_result
    assert "changes" in sim_result
    assert len(sim_result["changes"]) >= 2
    # Simulated score should be higher with +20% attendance, +2h study, +30% assignments
    assert sim_result["scenario"]["predicted_score"] >= sim_result["baseline"]["predicted_score"]

def test_subject_wise_prediction():
    predictor = StudentPredictor()
    student = {"student_id": "TEST_SUBJ", "attendance": 85.0, "cgpa": 8.0}
    subjs = predictor.predict_subject_wise(student, scale=20.0)
    assert len(subjs) == 5
    for s in subjs:
        assert "subject" in s
        assert "predicted_score" in s
        assert "interpretation" in s

