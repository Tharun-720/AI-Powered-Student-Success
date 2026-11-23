"""
Prediction & What-If Student Success Simulator for TREKVERSE Platform.
Allows students and faculty to simulate behavioral improvements and compare
model-generated baseline estimates with simulated scenarios (Section 4).
"""

import streamlit as st
import pandas as pd
import json
import os
import sys

PAGES_DIR = os.path.abspath(os.path.dirname(__file__))
APP_DIR = os.path.abspath(os.path.join(PAGES_DIR, ".."))
PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from database.database import get_student, list_students, get_student_by_user_id
from src.prediction.predictor import StudentPredictor
try:
    from app.ui_utils import apply_app_theme, render_brand_header, render_user_sidebar, require_auth, get_current_user
except ImportError:
    from ui_utils import apply_app_theme, render_brand_header, render_user_sidebar, require_auth, get_current_user

st.set_page_config(page_title="What-If Simulator | TREKVERSE", page_icon="🔮", layout="wide")
apply_app_theme()
render_user_sidebar()

if not require_auth(allowed_roles=["student", "faculty", "admin"]):
    st.stop()

current_user = get_current_user()

render_brand_header(
    title="What-If Student Success Scenario Simulator (Section 4)",
    subtitle="Simulate Academic Habit Adjustments, Attendance Improvements, and Study Commitments"
)

# Student selection
if current_user["role"] == "student":
    student = get_student_by_user_id(current_user["id"]) or get_student(current_user["username"].upper())
    selected_sid = student["student_id"]
else:
    all_sids = [s["student_id"] for s in list_students()]
    default_idx = all_sids.index("STU1024") if "STU1024" in all_sids else 0
    selected_sid = st.sidebar.selectbox("Select Student for Simulation", all_sids, index=default_idx)
    student = get_student(selected_sid)

if not student:
    st.error("Student record not found.")
    st.stop()

st.markdown(f"### Evaluating Scenario for: **{student['name']}** (`{student['student_id']}`)")
st.caption("Adjust the sliders below to explore how changes in attendance, study time, and assignment completion alter the model's estimate. *Original records remain completely unchanged.*")

predictor = StudentPredictor()

# Baseline Result
baseline_dict = dict(student)
# Default demo values if STU1024 to match PDF Section 4 illustrative baseline
if student["student_id"] == "STU1024":
    baseline_dict["attendance"] = 72.0
    baseline_dict["study_hours"] = 2.0
    baseline_dict["assignment_marks"] = 60.0

col_inputs, col_results = st.columns([5, 6])

with col_inputs:
    st.markdown("#### 🎛️ Scenario Input Controls")
    
    sim_att = st.slider(
        "Simulated Attendance (%)",
        min_value=40.0,
        max_value=100.0,
        value=min(100.0, float(baseline_dict.get("attendance", 75.0)) + 18.0),
        step=1.0,
        help="Target attendance rate across remaining semester weeks"
    )

    sim_study = st.slider(
        "Simulated Daily Study Commitment (hrs/day)",
        min_value=0.5,
        max_value=8.0,
        value=min(8.0, float(baseline_dict.get("study_hours", 2.0)) + 2.0),
        step=0.5,
        help="Self-study hours outside scheduled laboratory & classroom sessions"
    )

    sim_asg = st.slider(
        "Simulated Assignment Completion (%)",
        min_value=30.0,
        max_value=100.0,
        value=min(100.0, float(baseline_dict.get("assignment_completion", baseline_dict.get("assignment_marks", 60.0))) + 35.0),
        step=5.0,
        help="Target submission rate and accuracy for continuous assignments"
    )

    sim_internal = st.slider(
        "Simulated Continuous Internal Marks (%)",
        min_value=30.0,
        max_value=100.0,
        value=min(100.0, float(baseline_dict.get("cgpa", 7.0)) * 10.0),
        step=2.0,
        help="Projected mid-semester quiz and lab test performance"
    )

with col_results:
    st.markdown("#### 📊 Comparative Model Outcome")

    # Run What-If simulation
    sim_inputs = {
        "attendance": sim_att,
        "study_hours": sim_study,
        "assignment_marks": sim_asg,
        "assignment_completion": sim_asg,
        "internal_marks": sim_internal
    }
    
    sim_result = predictor.simulate_what_if(baseline_dict, sim_inputs, scale=20.0)

    base_score = sim_result["baseline"]["predicted_score"]
    scen_score = sim_result["scenario"]["predicted_score"]
    score_delta = sim_result["score_delta"]

    base_band = sim_result["baseline"]["risk_band"]
    scen_band = sim_result["scenario"]["risk_band"]

    res_c1, res_c2 = st.columns(2)

    with res_c1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Baseline Outcome</div>
            <div class="stat-value">{base_score:.1f} <span style="font-size: 1rem; color: #64748B;">/ 20.0</span></div>
            <div class="stat-subtext">Current Risk: <b>{base_band}</b></div>
        </div>
        """, unsafe_allow_html=True)

    with res_c2:
        delta_color = "#059669" if score_delta >= 0 else "#DC2626"
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Simulated Outcome</div>
            <div class="stat-value" style="color: {delta_color};">{scen_score:.1f} <span style="font-size: 1rem; color: #64748B;">/ 20.0</span></div>
            <div class="stat-subtext">Projected Risk: <b>{scen_band}</b> ({'+' if score_delta >= 0 else ''}{score_delta:.1f} pts)</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # Comparison Table matching PDF Section 4 format
    st.markdown("##### Parameter Adjustment Breakdown (Section 4)")
    comp_data = [
        {"Parameter": "Attendance", "Current Baseline": f"{baseline_dict.get('attendance', 0.0):.1f}%", "Scenario Value": f"{sim_att:.1f}%", "Delta": f"{'+' if sim_att >= baseline_dict.get('attendance', 0.0) else ''}{sim_att - baseline_dict.get('attendance', 0.0):.1f}%"},
        {"Parameter": "Daily Study Time", "Current Baseline": f"{baseline_dict.get('study_hours', 2.0):.1f} hrs/day", "Scenario Value": f"{sim_study:.1f} hrs/day", "Delta": f"{'+' if sim_study >= baseline_dict.get('study_hours', 2.0) else ''}{sim_study - baseline_dict.get('study_hours', 2.0):.1f}h"},
        {"Parameter": "Assignment Completion", "Current Baseline": f"{baseline_dict.get('assignment_completion', baseline_dict.get('assignment_marks', 60.0)):.1f}%", "Scenario Value": f"{sim_asg:.1f}%", "Delta": f"{'+' if sim_asg >= baseline_dict.get('assignment_completion', 60.0) else ''}{sim_asg - baseline_dict.get('assignment_completion', 60.0):.1f}%"},
        {"Parameter": "Predicted Assessment Score", "Current Baseline": f"{base_score:.1f} / 20", "Scenario Value": f"{scen_score:.1f} / 20", "Delta": f"{'+' if score_delta >= 0 else ''}{score_delta:.1f} pts"}
    ]
    st.dataframe(pd.DataFrame(comp_data), use_container_width=True, hide_index=True)

    st.success(sim_result["summary_statement"])

st.markdown("""
<div class="advisory-callout">
    <b>Estimation Notice (Section 4):</b> The scores above are model-generated estimates calculated using the trained ensemble pipeline. 
    They are not academic guarantees. Modifying scenario sliders does not alter the student's verified records in the database.
</div>
""", unsafe_allow_html=True)

