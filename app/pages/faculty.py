"""
Faculty Dashboard for TREKVERSE Student Success Platform.
Provides Early-Warning Queue, Student Diagnostic Detail View, Subject Analytics,
and Faculty Intervention & Follow-up Tracking.
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
    list_students, get_student, get_latest_prediction, get_student_marks,
    list_interventions, create_intervention, update_intervention, log_audit
)
from src.prediction.predictor import StudentPredictor
try:
    from app.ui_utils import apply_app_theme, render_brand_header, render_user_sidebar, require_auth, get_current_user
except ImportError:
    from ui_utils import apply_app_theme, render_brand_header, render_user_sidebar, require_auth, get_current_user

st.set_page_config(page_title="Faculty Console | TREKVERSE", page_icon="👨‍🏫", layout="wide")
apply_app_theme()
render_user_sidebar()

if not require_auth(allowed_roles=["faculty", "admin"]):
    st.stop()

current_user = get_current_user()

render_brand_header(
    title="Faculty Academic Advisory & Intervention Console",
    subtitle="Class Performance Monitoring, Early-Warning Queue, Diagnostic Explanations, and Intervention Tracking"
)

tab_queue, tab_detail, tab_interventions = st.tabs([
    "🚨 Early-Warning & Support Queue",
    "🔍 Student Diagnostic View",
    "📝 Faculty Interventions & Follow-ups"
])

# 1. Early-Warning Queue
with tab_queue:
    st.subheader("Student Progress & Early-Warning Directory (Section 3 & 5)")
    st.caption("Identify students who may benefit from timely academic support before final examinations:")

    # Filter Bar
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        dept_filter = st.selectbox("Department", ["All", "Computer Science", "Information Technology", "Electronics", "Data Science"], index=0)
    with fc2:
        sem_filter = st.selectbox("Semester", [0, 3, 4, 5, 6, 7], format_func=lambda x: "All Semesters" if x == 0 else f"Semester {x}", index=0)
    with fc3:
        risk_filter = st.selectbox("Risk Filter", ["All", "High Risk", "Moderate Risk", "Low Risk"], index=0)
    with fc4:
        search_q = st.text_input("Search ID or Name", placeholder="e.g. STU1024 or Sharma")

    students = list_students(
        department=dept_filter if dept_filter != "All" else None,
        semester=sem_filter if sem_filter != 0 else None,
        risk_band=risk_filter if risk_filter != "All" else None,
        search_query=search_q if search_q else None
    )

    # Summary Metrics for filtered cohort
    if students:
        df_students = pd.DataFrame(students)
        high_cnt = len(df_students[df_students["risk_band"] == "High Risk"])
        mod_cnt = len(df_students[df_students["risk_band"] == "Moderate Risk"])
        low_cnt = len(df_students[df_students["risk_band"] == "Low Risk"])
        avg_att = df_students["attendance"].mean()
        avg_cgpa = df_students["cgpa"].mean()

        qc1, qc2, qc3, qc4 = st.columns(4)
        qc1.metric("Students in Filter", len(df_students))
        qc2.metric("Requiring Support", f"{high_cnt + mod_cnt}", delta=f"{high_cnt} High Priority", delta_color="inverse")
        qc3.metric("Cohort Avg CGPA", f"{avg_cgpa:.2f} / 10.0")
        qc4.metric("Cohort Avg Attendance", f"{avg_att:.1f}%")

        st.markdown("---")

        # Table Display
        display_df = df_students[[
            "student_id", "name", "department", "semester", "cgpa", "attendance", "backlogs",
            "predicted_score", "risk_band"
        ]].copy()
        display_df.columns = [
            "Student ID", "Name", "Department", "Sem", "CGPA", "Attendance %", "Backlogs",
            "Predicted Score (/20)", "Risk Band"
        ]

        st.dataframe(
            display_df.style.apply(
                lambda col: [
                    "background-color: #FEE2E2; color: #991B1B; font-weight: bold;" if v == "High Risk"
                    else "background-color: #FEF3C7; color: #92400E; font-weight: bold;" if v == "Moderate Risk"
                    else "background-color: #D1FAE5; color: #065F46;" if v == "Low Risk"
                    else "" for v in col
                ],
                subset=["Risk Band"]
            ),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No student records match the selected filters.")

# 2. Student Diagnostic Detail View
with tab_detail:
    st.subheader("In-Depth Diagnostic & Explainable Evaluation (Section 5 & 6)")
    
    # Selection
    all_sids = [s["student_id"] for s in list_students()]
    default_idx = all_sids.index("STU1024") if "STU1024" in all_sids else 0
    selected_sid = st.selectbox("Select Student for Diagnostic Review", all_sids, index=default_idx)

    student = get_student(selected_sid)
    pred = get_latest_prediction(selected_sid)

    if student:
        predictor = StudentPredictor()
        if not pred:
            pred = predictor.predict_student(student, scale=20.0)

        # Overview Header
        st.markdown(f"### Student: **{student['name']}** (`{student['student_id']}`)")
        st.caption(f"{student['department']} · Semester {student['semester']}")

        col_p1, col_p2, col_p3, col_p4 = st.columns(4)
        
        band = pred.get("risk_band", "Moderate Risk")
        badge_class = "badge-high" if band == "High Risk" else "badge-mod" if band == "Moderate Risk" else "badge-low"

        with col_p1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Predicted Assessment Score</div>
                <div class="stat-value">{pred.get('predicted_score', 0.0)} <span style="font-size: 1rem; color: #64748B;">/ 20.0</span></div>
                <div class="stat-subtext">Statistical model forecast</div>
            </div>
            """, unsafe_allow_html=True)

        with col_p2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Early-Warning Risk Band</div>
                <div style="margin-top: 0.6rem;"><span class="{badge_class}">{band.upper()}</span></div>
                <div class="stat-subtext">Composite risk score: {pred.get('risk_score', 0.0):.2f}</div>
            </div>
            """, unsafe_allow_html=True)

        with col_p3:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Current Attendance</div>
                <div class="stat-value" style="color: {'#DC2626' if student['attendance'] < 75 else '#059669'};">{student['attendance']:.1f}%</div>
                <div class="stat-subtext">Mandatory barrier: 75%</div>
            </div>
            """, unsafe_allow_html=True)

        with col_p4:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Academic Standing</div>
                <div class="stat-value">{student['cgpa']:.2f} <span style="font-size: 1rem; color: #64748B;">/ 10</span></div>
                <div class="stat-subtext">{student['backlogs']} active backlog(s)</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)

        # Prediction Explanation (SHAP-aligned decomposition)
        expl_col1, expl_col2 = st.columns(2)
        explanation = pred.get("explanation", {})

        with expl_col1:
            st.markdown("#### Supporting Positive Indicators (+)")
            pos = explanation.get("top_positive", [])
            if pos:
                for p in pos:
                    st.success(f"**+{p['impact']:.2f} pts** — {p['description']}")
            else:
                st.info("No prominent positive accelerators detected.")

        with expl_col2:
            st.markdown("#### Primary Vulnerability & Risk Drivers (-)")
            neg = explanation.get("top_negative", [])
            if neg:
                for n in neg:
                    st.error(f"**{n['impact']:.2f} pts** — {n['description']}")
            else:
                st.success("No critical risk drivers identified.")

        # Subject-Wise Forecast (Section 6)
        st.markdown("#### Subject-Wise Diagnostic Forecast (Scale 20.0)")
        subj_preds = predictor.predict_subject_wise(student, scale=20.0)
        s_df = pd.DataFrame(subj_preds)
        s_display = s_df[["subject", "predicted_score", "interpretation"]].copy()
        s_display.columns = ["Subject Course", "Predicted Score (/20)", "Academic Diagnostic Interpretation"]
        st.dataframe(s_display, use_container_width=True, hide_index=True)

        # Faculty Action Recommendation Card
        st.markdown("""
        <div class="advisory-callout">
            <b>Suggested Next Step:</b> Coordinate a focused academic check-in with the student, review study commitments in 
            flagged subjects, and log an intervention plan below.
        </div>
        """, unsafe_allow_html=True)

# 3. Faculty Interventions Workflow
with tab_interventions:
    st.subheader("Intervention & Follow-up Action Tracker (Section 2 & 5)")
    st.caption("Track structured faculty support, scheduled check-ins, and student academic recovery progress:")

    with st.expander("➕ Log New Academic Intervention", expanded=False):
        with st.form("new_intervention_form"):
            ic1, ic2 = st.columns(2)
            with ic1:
                int_sid = st.selectbox("Target Student", all_sids, key="int_sid")
                int_status = st.selectbox("Initial Status", ["Open", "In Progress", "Resolved"])
            with ic2:
                int_issue = st.text_input("Identified Issue / Concern", placeholder="e.g. Attendance dipped below 70%, backlogs in DBMS")
                int_plan = st.text_area("Agreed Action Plan", placeholder="e.g. 1) Peer mentoring; 2) Weekly practice sets; 3) Fortnightly check-in")

            int_notes = st.text_input("Initial Faculty Remarks (Optional)")
            submitted_int = st.form_submit_button("Log Intervention Plan")
            if submitted_int:
                if not (int_issue and int_plan):
                    st.error("Please provide both issue summary and action plan.")
                else:
                    iid = create_intervention(int_sid, current_user["id"], int_issue, int_plan, int_notes, int_status)
                    log_audit(current_user["id"], "INTERVENTION_CREATED", f"Created intervention #{iid} for student {int_sid}")
                    st.success(f"Intervention recorded successfully for student {int_sid}!")
                    st.rerun()

    # List Interventions
    interventions = list_interventions()
    if interventions:
        int_df = pd.DataFrame(interventions)
        st.dataframe(
            int_df[["id", "student_id", "student_name", "department", "issue_summary", "action_plan", "status", "faculty_name", "updated_at"]],
            use_container_width=True,
            hide_index=True
        )

        st.markdown("#### Update Intervention Status")
        selected_iid = st.selectbox("Select Intervention ID to update", int_df["id"].tolist())
        target_int = int_df[int_df["id"] == selected_iid].iloc[0]

        with st.form(f"update_int_{selected_iid}"):
            u_col1, u_col2 = st.columns(2)
            with u_col1:
                new_status = st.selectbox("Status", ["Open", "In Progress", "Resolved"], index=["Open", "In Progress", "Resolved"].index(target_int["status"]))
            with u_col2:
                new_notes = st.text_area("Updated Faculty Remarks / Follow-up Notes", value=target_int.get("notes") or "")

            update_sub = st.form_submit_button("Update Intervention")
            if update_sub:
                update_intervention(selected_iid, new_status, new_notes)
                log_audit(current_user["id"], "INTERVENTION_UPDATED", f"Updated intervention #{selected_iid} to {new_status}")
                st.success(f"Intervention #{selected_iid} updated!")
                st.rerun()
    else:
        st.info("No active interventions recorded yet.")

