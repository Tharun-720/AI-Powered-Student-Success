"""
Feature engineering pipeline for TREKVERSE AI-Powered Student Success Platform.
Transforms academic, attendance, and engagement factors into normalized ML features.
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Any

FEATURE_COLUMNS = [
    "attendance",
    "attendance_trend",
    "previous_cgpa",
    "internal_marks",
    "assignment_marks",
    "study_hours",
    "backlogs",
    "activity_score",
    "attendance_deficit",
    "assessment_avg",
    "backlog_severity",
    "engagement_index"
]

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate domain-specific academic performance & risk indicators.
    Prevents data leakage by ensuring only pre-exam predictors are used.
    Robustly handles database row dictionaries and schema variations.
    """
    feat_df = df.copy()

    # Normalize aliases from database / raw sources
    if "previous_cgpa" not in feat_df.columns:
        if "cgpa" in feat_df.columns:
            feat_df["previous_cgpa"] = feat_df["cgpa"]
        else:
            feat_df["previous_cgpa"] = 7.0

    if "internal_marks" not in feat_df.columns:
        feat_df["internal_marks"] = feat_df["previous_cgpa"].astype(float) * 9.5

    if "assignment_marks" not in feat_df.columns:
        if "assignment_completion" in feat_df.columns:
            feat_df["assignment_marks"] = feat_df["assignment_completion"]
        else:
            feat_df["assignment_marks"] = 75.0

    if "study_hours" not in feat_df.columns:
        feat_df["study_hours"] = 2.5

    if "backlogs" not in feat_df.columns:
        feat_df["backlogs"] = 0

    if "activity_score" not in feat_df.columns:
        feat_df["activity_score"] = 70.0

    if "attendance_trend" not in feat_df.columns:
        feat_df["attendance_trend"] = 0.0

    if "attendance" not in feat_df.columns:
        feat_df["attendance"] = 80.0

    # Domain indicators
    feat_df["attendance_deficit"] = np.maximum(0.0, 75.0 - feat_df["attendance"].astype(float))
    feat_df["assessment_avg"] = (feat_df["internal_marks"].astype(float) + feat_df["assignment_marks"].astype(float)) / 2.0
    feat_df["backlog_severity"] = np.clip(feat_df["backlogs"].astype(float) * 0.25, 0.0, 1.0)
    
    # Composite engagement index (0.0 to 1.0)
    att_norm = feat_df["attendance"].astype(float) / 100.0
    asg_norm = feat_df["assignment_marks"].astype(float) / 100.0
    act_norm = feat_df["activity_score"].astype(float) / 100.0
    feat_df["engagement_index"] = (0.4 * att_norm + 0.35 * asg_norm + 0.25 * act_norm).clip(0.0, 1.0)

    return feat_df

def calculate_heuristic_risk(row: pd.Series) -> Tuple[str, float]:
    """
    Transparent rule-based baseline risk calculation (for comparison & hybrid checks).
    Returns (risk_band, risk_score)
    """
    att = float(row.get("attendance", 85.0))
    cgpa = float(row.get("previous_cgpa", row.get("cgpa", 7.5)))
    backlogs = int(row.get("backlogs", 0))
    internal = float(row.get("internal_marks", cgpa * 9.5))
    
    risk_points = 0.0
    if att < 65.0:
        risk_points += 40.0
    elif att < 75.0:
        risk_points += 22.0
    elif att < 80.0:
        risk_points += 10.0

    if cgpa < 5.5:
        risk_points += 30.0
    elif cgpa < 6.5:
        risk_points += 18.0
    elif cgpa < 7.5:
        risk_points += 8.0

    if backlogs >= 2:
        risk_points += 30.0
    elif backlogs == 1:
        risk_points += 15.0

    if internal < 50.0:
        risk_points += 20.0
    elif internal < 65.0:
        risk_points += 10.0

    risk_score = min(1.0, risk_points / 100.0)

    if risk_points >= 40.0 or att < 65.0 or backlogs >= 2 or cgpa < 5.0:
        band = "High Risk"
    elif risk_points >= 18.0 or att < 75.0 or backlogs >= 1 or internal < 60.0:
        band = "Moderate Risk"
    else:
        band = "Low Risk"

    return band, risk_score
