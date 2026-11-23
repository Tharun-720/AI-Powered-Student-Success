"""
Unit tests for ReportLab PDF generation module.
"""

import pytest
import io
from reports.report_generator import generate_student_pdf_report

def test_generate_student_pdf_report():
    student = {
        "student_id": "TEST_PDF_01",
        "name": "Jane Academic",
        "department": "Computer Science",
        "semester": 5,
        "cgpa": 8.1,
        "attendance": 84.0,
        "backlogs": 0,
        "study_hours": 3.0
    }
    pred = {
        "predicted_score": 15.6,
        "predicted_scale": 20.0,
        "risk_band": "Low Risk",
        "risk_score": 0.12,
        "model_version": "v1.0.0-test",
        "explanation": {
            "top_positive": [{"description": "High attendance at 84%", "impact": 1.2}],
            "top_negative": []
        }
    }
    subjs = [
        {"subject": "Mathematics", "predicted_score": 15.2, "interpretation": "Monitor progress"},
        {"subject": "Programming", "predicted_score": 17.1, "interpretation": "Potential strength"}
    ]
    recs = [
        {"category": "Topic Revision", "priority": "Medium", "text": "Review linear algebra concepts"}
    ]

    pdf_bytes = generate_student_pdf_report(
        student_data=student,
        prediction_data=pred,
        subject_scores=subjs,
        recommendations=recs,
        faculty_remarks="Student demonstrates steady performance."
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    # PDF magic number verification
    assert pdf_bytes.startswith(b"%PDF-")

