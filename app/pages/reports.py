"""
Automatic PDF Student Success Report Generator Page for TREKVERSE Platform.
Generates, renders, and provides downloadable official academic reports matching Section 10.
"""

import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime

PAGES_DIR = os.path.abspath(os.path.dirname(__file__))
APP_DIR = os.path.abspath(os.path.join(PAGES_DIR, ".."))
PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from database.database import (
    get_student, list_students, get_student_by_user_id, get_latest_prediction,
    get_student_recommendations, list_interventions
)
from src.prediction.predictor import StudentPredictor
from src.recommendations.recommender import generate_personalized_recommendations
from reports.report_generator import generate_student_pdf_report
try:
    from app.ui_utils import apply_app_theme, render_brand_header, render_user_sidebar, require_auth, get_current_user
except ImportError:
    from ui_utils import apply_app_theme, render_brand_header, render_user_sidebar, require_auth, get_current_user

st.set_page_config(page_title="PDF Reports | TREKVERSE", page_icon="📄", layout="wide")
apply_app_theme()
render_user_sidebar()

if not require_auth(allowed_roles=["student", "faculty", "admin"]):
    st.stop()

current_user = get_current_user()

render_brand_header(
    title="Official Student Success & Academic Guidance Report (Section 10)",
    subtitle="Downloadable Verified Academic Progress Summaries, AI Diagnostic Analysis, and Action Plans"
)

# Student selection
if current_user["role"] == "student":
    student = get_student_by_user_id(current_user["id"]) or get_student(current_user["username"].upper())
    selected_sid = student["student_id"]
else:
    all_sids = [s["student_id"] for s in list_students()]
    default_idx = all_sids.index("STU1024") if "STU1024" in all_sids else 0
    selected_sid = st.sidebar.selectbox("Select Target Student", all_sids, index=default_idx)
    student = get_student(selected_sid)

if not student:
    st.error("No student profile found.")
    st.stop()

predictor = StudentPredictor()
pred = get_latest_prediction(selected_sid)
if not pred:
    pred = predictor.predict_student(student, scale=20.0)

subject_scores = predictor.predict_subject_wise(student, scale=20.0)
recommendations = get_student_recommendations(selected_sid)
if not recommendations:
    recommendations = generate_personalized_recommendations(student, subject_scores)

# Look for faculty intervention notes
interventions = list_interventions(student_id=selected_sid)
faculty_remarks = interventions[0]["notes"] if interventions and interventions[0].get("notes") else "Continue monitoring subject progress and maintain study habits."

# Generate PDF in memory
pdf_bytes = generate_student_pdf_report(
    student_data=student,
    prediction_data=pred,
    subject_scores=subject_scores,
    recommendations=recommendations,
    faculty_remarks=faculty_remarks
)

# Actions Bar
act_col1, act_col2 = st.columns([4, 2])
with act_col1:
    st.markdown(f"### Report Preview: **{student['name']}** (`{student['student_id']}`)")
    st.caption(f"Evaluation Period: Fall Semester · Department of {student['department']} · Model: {pred.get('model_version', 'v1.0.0-ensemble')}")

with act_col2:
    st.download_button(
        label="⬇️ Download Official PDF Report",
        data=pdf_bytes,
        file_name=f"TREKVERSE_Academic_Report_{student['student_id']}.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True
    )

st.divider()

# On-Screen Structured Preview Matching Section 10 Table
st.markdown("#### 1. Header & Institutional Identification")
st.info(f"**TREKVERSE AI ACADEMY — Student Success & Academic Guidance Report**\n\n*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} | Document ID: TV-{student['student_id']}-{datetime.now().strftime('%Y%m')}*")

st.markdown("#### 2. Student Demographics & Academic Indicators")
p_col1, p_col2, p_col3, p_col4 = st.columns(4)
p_col1.metric("Student ID", student["student_id"])
p_col2.metric("Department / Sem", f"{student['department']} (Sem {student['semester']})")
p_col3.metric("Cumulative CGPA", f"{student['cgpa']:.2f} / 10.0")
p_col4.metric("Semester Attendance", f"{student['attendance']:.1f}%", delta="Normal" if student["attendance"] >= 75 else "- Below 75% Cutoff", delta_color="normal" if student["attendance"] >= 75 else "inverse")

st.markdown("#### 3. AI Predictive Analysis & Early-Warning Risk Assessment")
a_col1, a_col2 = st.columns(2)
with a_col1:
    st.markdown(f"**Predicted Assessment Score:** `{pred.get('predicted_score', 0.0)} / 20.0`")
    st.markdown(f"**Early-Warning Risk Band:** `{pred.get('risk_band')}` (Score: {pred.get('risk_score', 0.0):.2f})")
with a_col2:
    explanation = pred.get("explanation", {})
    st.markdown("**Top Supporting Factors:**")
    for pos in explanation.get("top_positive", [])[:2]:
        st.write(f"• +{pos['impact']:.2f} pts: {pos['description']}")
    st.markdown("**Top Vulnerability Factors:**")
    for neg in explanation.get("top_negative", [])[:2]:
        st.write(f"• {neg['impact']:.2f} pts: {neg['description']}")

st.markdown("#### 4. Subject-Wise Diagnostic Forecast")
subj_df = pd.DataFrame(subject_scores)[["subject", "predicted_score", "interpretation"]]
subj_df.columns = ["Subject Course", "Predicted Score (/20)", "Diagnostic Interpretation"]
st.dataframe(subj_df, use_container_width=True, hide_index=True)

st.markdown("#### 5. Personalized Learning Guidance & Faculty Remarks")
rec_df = pd.DataFrame(recommendations)[["priority", "category", "text" if "text" in recommendations[0] else "recommendation_text"]]
rec_df.columns = ["Priority", "Category", "Guidance Action Plan"]
st.dataframe(rec_df, use_container_width=True, hide_index=True)

st.markdown(f"**Faculty Remarks:** *\"{faculty_remarks}\"*")

st.markdown("#### 6. Official Advisory Disclaimer")
st.markdown("""
<div class="advisory-callout">
    <b>Disclaimer:</b> Model output is an empirical estimate and should be reviewed with actual academic context. 
    Predictions support human review and timely guidance—not replace faculty judgment.
</div>
""", unsafe_allow_html=True)

