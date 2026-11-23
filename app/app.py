"""
Main Application Entrypoint for TREKVERSE AI-Powered Student Success Platform.
Provides authentication, institutional KPI overview, and role-based routing.
"""

import streamlit as st
import os
import sys

# Ensure project root and app dir are in sys.path
APP_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from database.database import (
    init_db, authenticate_user, get_dashboard_summary, list_students
)
try:
    from app.ui_utils import apply_app_theme, render_brand_header, render_user_sidebar
except ImportError:
    from ui_utils import apply_app_theme, render_brand_header, render_user_sidebar

st.set_page_config(
    page_title="TREKVERSE | Student Success Prediction & Guidance",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply global styling
apply_app_theme()
render_user_sidebar()

# Initialize DB if not present
init_db()

# Session State for User Auth
if "user" not in st.session_state:
    st.session_state["user"] = None

# Header Banner
render_brand_header(
    title="AI-Powered Student Success Prediction & Academic Guidance System",
    subtitle="Enterprise Academic Progress Analytics, Early-Warning Risk Forecasting, and Personalized Learning Guidance"
)

# Login & Role Management Section
if not st.session_state["user"]:
    st.markdown("### 🔐 Institutional Portal Sign-In")
    st.caption("Sign in with your role-based credentials or select a demonstration account below:")

    demo_col1, demo_col2, demo_col3 = st.columns(3)
    with demo_col1:
        if st.button("🛡️ Sign In as Administrator", use_container_width=True, help="Full system governance, dataset imports, user & model management"):
            user = authenticate_user("admin", "admin123")
            if user:
                st.session_state["user"] = user
                st.rerun()

    with demo_col2:
        if st.button("👨‍🏫 Sign In as Faculty (Prof. Sharma)", use_container_width=True, help="Classroom analytics, early-warning queue, and intervention tracking"):
            user = authenticate_user("prof_sharma", "faculty123")
            if user:
                st.session_state["user"] = user
                st.rerun()

    with demo_col3:
        if st.button("🎓 Sign In as Student (STU1024 - Kavya)", use_container_width=True, help="Student profile, AI recommendations, weekly study planner, and report download"):
            user = authenticate_user("stu1024", "student123")
            if user:
                st.session_state["user"] = user
                st.rerun()

    with st.expander("Or enter manual credentials"):
        with st.form("login_form"):
            uname = st.text_input("Username", placeholder="e.g. admin or stu1024")
            pwd = st.text_input("Password", type="password", placeholder="Enter account password")
            submit = st.form_submit_button("Sign In")
            if submit:
                auth = authenticate_user(uname.strip(), pwd.strip())
                if auth:
                    st.session_state["user"] = auth
                    st.success(f"Welcome back, {auth['full_name']}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

    st.divider()

# Live Dashboard Summary Stats (Directly Reflects PDF Section 3 & Section 12)
summary = get_dashboard_summary()

st.markdown("### 📊 Institutional Performance & Monitoring Dashboard")
st.caption("Real-time aggregates calculated directly from active institutional records.")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Total Monitored Students</div>
        <div class="stat-value">{summary['total_students']}</div>
        <div class="stat-subtext">Active semester enrollment</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Average Institutional CGPA</div>
        <div class="stat-value">{summary['avg_cgpa']:.2f} <span style="font-size: 1rem; color: #64748B;">/ 10.0</span></div>
        <div class="stat-subtext">Historical semester cumulative</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Students Requiring Support</div>
        <div class="stat-value" style="color: #DC2626;">{summary['requiring_support']}</div>
        <div class="stat-subtext">{summary['high_risk']} High Risk · {summary['moderate_risk']} Moderate</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Average Attendance Rate</div>
        <div class="stat-value" style="color: #059669;">{summary['avg_attendance']:.1f}%</div>
        <div class="stat-subtext">Mandatory threshold: 75.0%</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)

# Navigation Directory Cards
st.markdown("### 🧭 Platform Capabilities & Modules")
st.caption("Access specialized tools according to your institutional authorization level:")

m_col1, m_col2, m_col3 = st.columns(3)

with m_col1:
    st.markdown("""
    **👨‍🏫 Faculty Operations & Interventions**
    - **At-Risk Queue:** Early identification of learning needs and attendance shortfalls.
    - **Intervention Tracking:** Record actionable follow-up plans, notes, and resolution statuses.
    - **Class Analytics:** Subject-wise performance diagnostic and student comparisons.
    """)
    if st.button("Open Faculty Dashboard →", key="nav_fac", use_container_width=True):
        st.switch_page("pages/faculty.py")

with m_col2:
    st.markdown("""
    **🎓 Student Success & Guidance**
    - **Academic Profile:** Semester trends, current CGPA, and estimated academic outcomes.
    - **Personalized Planner:** Weekly calendar matching available study hours and weak subjects.
    - **PDF Progress Report:** Instant downloadable official report for academic reviews.
    """)
    if st.button("Open Student Dashboard →", key="nav_stu", use_container_width=True):
        st.switch_page("pages/student.py")

with m_col3:
    st.markdown("""
    **🔮 What-If Simulator & Model Analytics**
    - **Interactive Simulator:** Test scenario adjustments (attendance, study hours, assignments).
    - **Model Explainability:** SHAP-aligned positive and negative factor attribution.
    - **Deep Analytics:** Cohort clustering personas and risk migration trends.
    """)
    if st.button("Open What-If Simulator →", key="nav_sim", use_container_width=True):
        st.switch_page("pages/prediction.py")

st.markdown("""
<div class="advisory-callout">
    <b>Responsible AI Deployment Note:</b> Predictions provide timely, data-backed decision support for academic advisors. 
    They do not replace faculty judgment and must not serve as the sole criterion for progression, grading, or academic penalties.
</div>
""", unsafe_allow_html=True)

