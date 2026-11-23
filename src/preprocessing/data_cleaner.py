"""
Data cleaning and validation module for TREKVERSE AI-Powered Student Success Platform.
Provides schema validation, range checks, missing value handling, and column mapping.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional

CANONICAL_COLUMNS = {
    "student_id": ["student_id", "student id", "id", "roll_no", "reg_no", "registration_no"],
    "name": ["name", "student_name", "full_name"],
    "department": ["department", "dept", "branch", "stream"],
    "semester": ["semester", "sem", "term"],
    "attendance": ["attendance", "attendance_pct", "attendance_percentage", "att_pct"],
    "attendance_trend": ["attendance_trend", "att_trend", "trend"],
    "previous_cgpa": ["previous_cgpa", "prev_cgpa", "cgpa", "gpa"],
    "internal_marks": ["internal_marks", "internal", "internals", "cie"],
    "assignment_marks": ["assignment_marks", "assignment", "assignments", "assignment_completion"],
    "study_hours": ["study_hours", "study_time", "hours_per_day", "daily_study_hours"],
    "backlogs": ["backlogs", "arrears", "failures", "past_failures"],
    "activity_score": ["activity_score", "platform_activity", "lms_activity", "engagement_score"],
    "final_marks": ["final_marks", "final_score", "exam_score", "grade_score", "target"]
}

def auto_detect_column_mapping(df_columns: List[str]) -> Dict[str, str]:
    """Auto-detect mapping between incoming file headers and canonical schema."""
    mapping = {}
    lower_cols = {col.strip().lower().replace(" ", "_"): col for col in df_columns}
    
    for canon, aliases in CANONICAL_COLUMNS.items():
        found = False
        for alias in aliases:
            cleaned_alias = alias.lower().replace(" ", "_")
            if cleaned_alias in lower_cols:
                mapping[canon] = lower_cols[cleaned_alias]
                found = True
                break
        if not found:
            for c in df_columns:
                if canon in c.lower():
                    mapping[canon] = c
                    break
    return mapping

def validate_and_clean_data(
    df: pd.DataFrame,
    column_mapping: Optional[Dict[str, str]] = None,
    allow_missing_target: bool = True
) -> Tuple[pd.DataFrame, List[Dict[str, Any]], Dict[str, Any]]:
    """
    Validates uploaded dataset against requirements.
    Returns: (cleaned_df, row_errors, summary_stats)
    """
    errors: List[Dict[str, Any]] = []
    summary = {
        "total_rows": len(df),
        "valid_rows": 0,
        "rejected_rows": 0,
        "warnings": []
    }
    
    if column_mapping:
        inv_map = {v: k for k, v in column_mapping.items() if v in df.columns}
        df_renamed = df.rename(columns=inv_map).copy()
    else:
        mapping = auto_detect_column_mapping(list(df.columns))
        inv_map = {v: k for k, v in mapping.items()}
        df_renamed = df.rename(columns=inv_map).copy()

    # Check required primary key
    if "student_id" not in df_renamed.columns:
        errors.append({"row": 0, "field": "student_id", "message": "Missing required field: Student_ID."})
        summary["rejected_rows"] = len(df)
        return pd.DataFrame(), errors, summary

    valid_indices = []
    seen_ids = set()

    for idx, row in df_renamed.iterrows():
        row_num = idx + 1
        row_has_error = False
        sid = str(row.get("student_id", "")).strip()

        if not sid or sid.lower() == "nan":
            errors.append({"row": row_num, "field": "student_id", "message": "Student ID cannot be empty."})
            row_has_error = True
        elif sid in seen_ids:
            errors.append({"row": row_num, "field": "student_id", "message": f"Duplicate Student ID '{sid}'."})
            row_has_error = True
        else:
            seen_ids.add(sid)

        # Attendance check (0 - 100)
        att = row.get("attendance", np.nan)
        try:
            att_val = float(att)
            if not (0.0 <= att_val <= 100.0):
                errors.append({"row": row_num, "field": "attendance", "message": f"Attendance {att_val}% out of range [0, 100]."})
                row_has_error = True
        except (ValueError, TypeError):
            errors.append({"row": row_num, "field": "attendance", "message": f"Invalid numeric attendance: {att}."})
            row_has_error = True

        # CGPA check (0 - 10)
        cgpa = row.get("previous_cgpa", np.nan)
        try:
            cgpa_val = float(cgpa)
            if not (0.0 <= cgpa_val <= 10.0):
                errors.append({"row": row_num, "field": "previous_cgpa", "message": f"CGPA {cgpa_val} out of scale [0, 10]."})
                row_has_error = True
        except (ValueError, TypeError):
            errors.append({"row": row_num, "field": "previous_cgpa", "message": f"Invalid numeric CGPA: {cgpa}."})
            row_has_error = True

        # Study hours (non-negative, plausibility warning)
        sh = row.get("study_hours", 2.0)
        try:
            sh_val = float(sh)
            if sh_val < 0.0:
                errors.append({"row": row_num, "field": "study_hours", "message": "Study hours cannot be negative."})
                row_has_error = True
            elif sh_val > 16.0:
                summary["warnings"].append(f"Row {row_num}: Study hours ({sh_val}h/day) is unusually high; flagged for review.")
        except (ValueError, TypeError):
            errors.append({"row": row_num, "field": "study_hours", "message": f"Invalid study hours: {sh}."})
            row_has_error = True

        # Backlogs (non-negative integer)
        backlogs = row.get("backlogs", 0)
        try:
            bl_val = int(backlogs)
            if bl_val < 0:
                errors.append({"row": row_num, "field": "backlogs", "message": "Backlogs cannot be negative."})
                row_has_error = True
        except (ValueError, TypeError):
            errors.append({"row": row_num, "field": "backlogs", "message": f"Invalid backlogs count: {backlogs}."})
            row_has_error = True

        # Final marks if provided
        if not allow_missing_target and "final_marks" in df_renamed.columns:
            fm = row.get("final_marks", np.nan)
            try:
                fm_val = float(fm)
                if not (0.0 <= fm_val <= 100.0):
                    errors.append({"row": row_num, "field": "final_marks", "message": f"Final marks {fm_val} outside [0, 100]."})
                    row_has_error = True
            except (ValueError, TypeError):
                errors.append({"row": row_num, "field": "final_marks", "message": f"Invalid final marks: {fm}."})
                row_has_error = True

        if not row_has_error:
            valid_indices.append(idx)

    summary["valid_rows"] = len(valid_indices)
    summary["rejected_rows"] = len(df) - len(valid_indices)

    cleaned_df = df_renamed.loc[valid_indices].copy()
    
    # Impute missing and standard defaults
    if "name" not in cleaned_df.columns:
        cleaned_df["name"] = [f"Student {s}" for s in cleaned_df["student_id"]]
    else:
        cleaned_df["name"] = cleaned_df["name"].fillna("Unknown Student")

    if "department" not in cleaned_df.columns:
        cleaned_df["department"] = "Computer Science"
    else:
        cleaned_df["department"] = cleaned_df["department"].fillna("Computer Science")

    if "semester" not in cleaned_df.columns:
        cleaned_df["semester"] = 5
    else:
        cleaned_df["semester"] = cleaned_df["semester"].fillna(5).astype(int)

    if "internal_marks" not in cleaned_df.columns:
        cleaned_df["internal_marks"] = cleaned_df["previous_cgpa"] * 9.5
    else:
        cleaned_df["internal_marks"] = cleaned_df["internal_marks"].fillna(cleaned_df["previous_cgpa"] * 9.5)

    if "assignment_marks" not in cleaned_df.columns:
        cleaned_df["assignment_marks"] = cleaned_df["attendance"] * 0.85
    else:
        cleaned_df["assignment_marks"] = cleaned_df["assignment_marks"].fillna(cleaned_df["attendance"] * 0.85)

    if "attendance_trend" not in cleaned_df.columns:
        cleaned_df["attendance_trend"] = 0.0
    else:
        cleaned_df["attendance_trend"] = cleaned_df["attendance_trend"].fillna(0.0)

    if "activity_score" not in cleaned_df.columns:
        cleaned_df["activity_score"] = (cleaned_df["attendance"] * 0.5 + cleaned_df["assignment_marks"] * 0.5).clip(0, 100)
    else:
        cleaned_df["activity_score"] = cleaned_df["activity_score"].fillna(70.0)

    return cleaned_df, errors, summary

