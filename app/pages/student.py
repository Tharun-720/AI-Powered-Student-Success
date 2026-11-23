"""
Student Dashboard for TREKVERSE Student Success Platform.
Provides personalized academic progress monitoring, explainable predictions,
AI-Personalized Learning Planner, and report downloads.
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

from database.database import (
    get_student, get_student_by_user_id, get_latest_prediction, get_study_plans,
    save_study_plan_task, toggle_study_task, clear_study_plan, list_students
)
from src.prediction.predictor import StudentPredictor
from src.recommendations.recommender import (
    generate_personalized_recommendations, build_weekly_study_schedule
)
from reports.report_generator import generate_student_pdf_report
try:
    from app.ui_utils import apply_app_theme, render_brand_header, render_user_sidebar, require_auth, get_current_user
except ImportError:
    from ui_utils import apply_app_theme, render_brand_header, render_user_sidebar, require_auth, get_current_user

st.set_page_config(page_title="Student Portal | TREKVERSE", page_icon="🎓", layout="wide")
apply_app_theme()
render_user_sidebar()

if not require_auth(allowed_roles=["student", "faculty", "admin"]):
    st.stop()

current_user = get_current_user()

# Student Authorization Check (Students can ONLY view their own profile)
if current_user["role"] == "student":
    student = get_student_by_user_id(current_user["id"])
    if not student:
        # Fallback by matching username e.g. "stu1024" -> "STU1024"
        student = get_student(current_user["username"].upper())
    if not student:
        st.error("No student profile linked to your user account. Please contact the administrator.")
        st.stop()
    selected_sid = student["student_id"]
else:
    # Faculty/Admin can view any student profile
    all_sids = [s["student_id"] for s in list_students()]
    default_idx = all_sids.index("STU1024") if "STU1024" in all_sids else 0
    selected_sid = st.sidebar.selectbox("Preview Student", all_sids, index=default_idx)
    student = get_student(selected_sid)

render_brand_header(
    title=f"Student Academic Progress & Learning Studio",
    subtitle=f"Welcome, {student['name']} ({student['student_id']}) · {student['department']} (Semester {student['semester']})"
)

# Fetch latest prediction
predictor = StudentPredictor()
pred = get_latest_prediction(selected_sid)
if not pred:
    pred = predictor.predict_student(student, scale=20.0)

# 1. Top Metrics Cards
c1, c2, c3, c4 = st.columns(4)

band = pred.get("risk_band", "Low Risk")
badge_class = "badge-high" if band == "High Risk" else "badge-mod" if band == "Moderate Risk" else "badge-low"

with c1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Estimated Final Score</div>
        <div class="stat-value">{pred.get('predicted_score', 0.0)} <span style="font-size: 1rem; color: #64748B;">/ 20.0</span></div>
        <div class="stat-subtext">AI-forecasted outcome</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Academic Status Band</div>
        <div style="margin-top: 0.6rem;"><span class="{badge_class}">{band.upper()}</span></div>
        <div class="stat-subtext">Early-guidance risk estimate</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Cumulative GPA</div>
        <div class="stat-value">{student['cgpa']:.2f} <span style="font-size: 1rem; color: #64748B;">/ 10</span></div>
        <div class="stat-subtext">{student['backlogs']} active backlogs</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Semester Attendance</div>
        <div class="stat-value" style="color: {'#DC2626' if student['attendance'] < 75 else '#059669'};">{student['attendance']:.1f}%</div>
        <div class="stat-subtext">Regulatory requirement: 75%</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)

# 2. Main Studio Tabs
tab_overview, tab_planner, tab_forecast = st.tabs([
    "📈 Academic Progress & Diagnostic",
    "📅 AI-Personalized Learning Planner (Section 11)",
    "🎯 Subject-Wise Forecast & Quick Actions"
])

# Overview Tab
with tab_overview:
    col_l, col_r = st.columns([3, 2])

    with col_l:
        st.subheader("Contributing Factors Influencing Your Forecast")
        explanation = pred.get("explanation", {})
        pos = explanation.get("top_positive", [])
        neg = explanation.get("top_negative", [])

        if pos:
            st.markdown("**Supporting Accelerators (+):**")
            for p in pos:
                st.success(f"**+{p['impact']:.2f} pts** — {p['description']}")

        if neg:
            st.markdown("**Key Areas Needing Attention (-):**")
            for n in neg:
                st.error(f"**{n['impact']:.2f} pts** — {n['description']}")

        st.caption("ℹ️ *Attribution metrics reflect correlated historical learning factors, not guaranteed outcomes.*")

    with col_r:
        st.subheader("Quick Actions & Downloads")
        st.markdown("""
        Explore how small habit adjustments can improve your final grade, or download an official PDF progress report:
        """)
        
        # Download PDF Directly
        subj_scores = predictor.predict_subject_wise(student, scale=20.0)
        recs = generate_personalized_recommendations(student, subj_scores)
        pdf_bytes = generate_student_pdf_report(student, pred, subj_scores, recs)

        st.download_button(
            label="📄 Download Official Student Success Report (PDF)",
            data=pdf_bytes,
            file_name=f"TREKVERSE_Report_{student['student_id']}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

        if st.button("🔮 Open What-If Scenario Simulator →", use_container_width=True):
            st.switch_page("pages/prediction.py")

# Learning Planner Tab (Section 11)
with tab_planner:
    st.subheader("AI-Personalized Learning Planner (Section 11)")
    st.markdown("""
    Your customized weekly learning schedule is generated dynamically based on your identified weak subjects, 
    upcoming continuous assessments, and available study hours.
    """)

    # Get current saved study plans from DB
    existing_plans = get_study_plans(selected_sid)

    # Regeneration controls
    with st.expander("⚙️ Adjust Weekly Study Goals & Re-generate Plan", expanded=len(existing_plans) == 0):
        with st.form("regen_plan_form"):
            gc1, gc2 = st.columns(2)
            with gc1:
                study_hrs = st.slider("Available Daily Study Time (hours/day)", min_value=1.0, max_value=6.0, value=max(1.5, student["study_hours"]), step=0.5)
            with gc2:
                target_score = st.slider("Target Assessment Score (/20)", min_value=12.0, max_value=20.0, value=17.0, step=0.5)

            regen_submit = st.form_submit_button("Generate Tailored Weekly Plan")
            if regen_submit:
                clear_study_plan(selected_sid)
                subj_preds = predictor.predict_subject_wise(student, scale=20.0)
                weak_subjs = [s["subject"] for s in subj_preds if s["interpretation"] == "May need targeted practice"]
                if not weak_subjs:
                    weak_subjs = ["DBMS", "Mathematics", "Electronics"]
                new_tasks = build_weekly_study_schedule(student, weak_subjs, daily_available_hours=study_hrs)
                for t in new_tasks:
                    save_study_plan_task(
                        student_id=selected_sid,
                        day_of_week=t["day_of_week"],
                        subject=t["subject"],
                        activity=t["activity"],
                        duration_hours=t["duration_hours"],
                        time_slot=t["time_slot"]
                    )
                st.success("New personalized weekly study schedule generated!")
                st.rerun()

    # Display Current Interactive Plan
    plans = get_study_plans(selected_sid)
    if plans:
        st.markdown("#### This Week's Actionable Schedule")
        
        # Group by day
        for p in plans:
            p_id = p["id"]
            is_done = bool(p["completed"])
            col_chk, col_txt = st.columns([1, 11])
            with col_chk:
                chk = st.checkbox("", value=is_done, key=f"chk_task_{p_id}")
                if chk != is_done:
                    toggle_study_task(p_id, chk)
                    st.rerun()
            with col_txt:
                strike_start = "~~" if is_done else ""
                strike_end = "~~" if is_done else ""
                badge = "✅ COMPLETED" if is_done else f"⏳ {p['duration_hours']}h ({p['time_slot']})"
                st.markdown(f"**{p['day_of_week']}** · `{p['subject']}` · {badge}\n\n{strike_start}{p['activity']}{strike_end}")
            st.divider()

        # Add Custom Task Form
        with st.expander("➕ Add Personal Study Milestone"):
            with st.form("custom_task_form"):
                tc1, tc2 = st.columns(2)
                with tc1:
                    c_day = st.selectbox("Day of Week", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
                    c_subj = st.selectbox("Subject", ["DBMS", "Mathematics", "Programming", "Computer Networks", "Electronics", "General"])
                with tc2:
                    c_act = st.text_input("Task Description", placeholder="e.g. Solve 5 SQL join practice queries")
                    c_dur = st.number_input("Duration (hours)", min_value=0.5, max_value=4.0, value=1.0, step=0.5)
                
                c_submit = st.form_submit_button("Add Task")
                if c_submit and c_act:
                    save_study_plan_task(selected_sid, c_day, c_subj, c_act, c_dur)
                    st.success("Task added to your schedule!")
                    st.rerun()
    else:
        st.info("No active study plan saved yet. Click the expander above to generate your tailored schedule!")

# Subject Forecast Tab (Section 6)
with tab_forecast:
    st.subheader("Subject-Wise Forecast & Diagnostic Interpretation (Section 6)")
    st.caption("Estimated subject-level performance derived from your assessment history:")

    subj_preds = predictor.predict_subject_wise(student, scale=20.0)
    for sp in subj_preds:
        scol1, scol2, scol3 = st.columns([2, 2, 4])
        with scol1:
            st.markdown(f"**{sp['subject']}**")
        with scol2:
            st.markdown(f"<font size=4><b>{sp['predicted_score']:.1f}</b></font> / 20.0", unsafe_allow_html=True)
        with scol3:
            badge_color = sp["badge_color"]
            st.markdown(f"<span style='color: {badge_color}; font-weight: bold;'>● {sp['interpretation']}</span>", unsafe_allow_html=True)
        st.divider()

    st.markdown("""
    <div class="advisory-callout">
        <b>Study Tip:</b> Focus revision efforts on subjects flagged with <i>"May need targeted practice"</i>. 
        Allocate your primary weekday study blocks (Monday & Tuesday) to those foundational topics.
    </div>
    """, unsafe_allow_html=True)

