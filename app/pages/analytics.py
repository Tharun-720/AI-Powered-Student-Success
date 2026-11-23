"""
Deep Analytics & Student Segmentation Dashboard for TREKVERSE Platform.
Provides cohort analytics, attendance vs assessment correlation, subject distributions,
and K-Means student clustering personas (Section 5, 6, 11).
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

PAGES_DIR = os.path.abspath(os.path.dirname(__file__))
APP_DIR = os.path.abspath(os.path.join(PAGES_DIR, ".."))
PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from database.database import list_students
from src.clustering.student_segmentation import SEGMENT_PERSONAS
try:
    from app.ui_utils import apply_app_theme, render_brand_header, render_user_sidebar, require_auth
except ImportError:
    from ui_utils import apply_app_theme, render_brand_header, render_user_sidebar, require_auth

st.set_page_config(page_title="Analytics Studio | TREKVERSE", page_icon="📈", layout="wide")
apply_app_theme()
render_user_sidebar()

if not require_auth(allowed_roles=["faculty", "admin", "student"]):
    st.stop()

render_brand_header(
    title="Institutional Learning Analytics & Student Segmentation",
    subtitle="Cohort Trend Analysis, Attendance vs Assessment Correlation, and Unsupervised Learning Personas"
)

students = list_students()
if not students:
    st.warning("No student records available for analytics.")
    st.stop()

df = pd.DataFrame(students)

# 1. High-Level Visual Overview
c_row1, c_row2 = st.columns(2)

with c_row1:
    st.subheader("Early-Warning Risk Band Distribution")
    risk_counts = df["risk_band"].value_counts().reset_index()
    risk_counts.columns = ["Risk Band", "Count"]

    color_map = {
        "Low Risk": "#10B981",       # Green
        "Moderate Risk": "#F59E0B",  # Amber
        "High Risk": "#EF4444"       # Red
    }

    fig_pie = px.pie(
        risk_counts,
        names="Risk Band",
        values="Count",
        color="Risk Band",
        color_discrete_map=color_map,
        hole=0.45,
        title="Student Cohort Risk Breakdown"
    )
    fig_pie.update_traces(textinfo="percent+label", textposition="inside")
    st.plotly_chart(fig_pie, use_container_width=True)

with c_row2:
    st.subheader("Attendance vs Assessment Performance")
    fig_scatter = px.scatter(
        df,
        x="attendance",
        y="cgpa",
        color="risk_band",
        color_discrete_map=color_map,
        hover_data=["student_id", "name", "backlogs", "predicted_score"],
        labels={"attendance": "Attendance Percentage (%)", "cgpa": "Cumulative GPA (/10.0)"},
        title="Correlation: Attendance Rate vs Academic GPA"
    )
    # Add 75% attendance threshold line
    fig_scatter.add_vline(x=75.0, line_dash="dash", line_color="#DC2626", annotation_text="75% Mandatory Barrier", annotation_position="top left")
    st.plotly_chart(fig_scatter, use_container_width=True)

st.divider()

# 2. Semester & Department Comparisons
st.subheader("Semester-wise CGPA and Performance Distributions (Section 6)")
c_sem1, c_sem2 = st.columns(2)

with c_sem1:
    fig_box = px.box(
        df,
        x="semester",
        y="cgpa",
        color="department",
        labels={"semester": "Semester", "cgpa": "Cumulative GPA"},
        title="CGPA Spread Across Departments & Semesters"
    )
    st.plotly_chart(fig_box, use_container_width=True)

with c_sem2:
    fig_hist = px.histogram(
        df,
        x="predicted_score",
        nbins=25,
        color="risk_band",
        color_discrete_map=color_map,
        labels={"predicted_score": "Predicted Assessment Score (/20.0)"},
        title="Model Score Distribution Across Monitored Population"
    )
    st.plotly_chart(fig_hist, use_container_width=True)

st.divider()

# 3. Student Segmentation & Personas (Section 11)
st.subheader("Unsupervised Student Segmentation & Learning Personas (Section 11)")
st.markdown("""
Using **K-Means clustering** across engagement, attendance, continuous assessment, and study commitment factors, 
the platform discovers natural student cohorts to tailor institutional support programs.
""")

persona_cols = st.columns(4)
for i in range(4):
    p = SEGMENT_PERSONAS[i]
    with persona_cols[i]:
        st.markdown(f"""
        <div class="stat-card" style="min-height: 250px;">
            <div class="stat-label">Persona Cluster {i+1}</div>
            <div style="font-weight: 700; font-size: 1.05rem; color: #1E3A8A; margin-top: 0.35rem;">{p['title']}</div>
            <p style="font-size: 0.8rem; color: #475569; margin-top: 0.5rem;">{p['description']}</p>
            <hr style="margin: 0.5rem 0; border: none; border-top: 1px solid #E2E8F0;"/>
            <div style="font-size: 0.78rem; color: #0F172A;"><b>Action:</b> {p['recommended_action']}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("""
<div class="advisory-callout" style="margin-top: 1.5rem;">
    <b>Cautious Academic Interpretation Note (Section 11):</b> 
    Cluster assignments represent behavioral tendencies based on available data. They are non-deterministic groupings 
    designed to identify program-level support strategies—not definitive labels or evaluative rankings of student aptitude.
</div>
""", unsafe_allow_html=True)

