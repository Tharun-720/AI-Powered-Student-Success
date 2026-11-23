"""
Administrator Dashboard for TREKVERSE Student Success Platform.
Handles User Management, Dataset Import & Validation Studio, Model Registry Monitoring,
Configurable Risk Thresholds, and System Audit Logs.
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
    list_users, create_user, get_setting, set_setting, get_recent_audit_logs,
    log_audit, upsert_student, list_students
)
from src.preprocessing.data_cleaner import validate_and_clean_data, auto_detect_column_mapping
from src.training.model_trainer import train_and_evaluate_models, MODEL_REGISTRY_DIR
from src.prediction.predictor import StudentPredictor
try:
    from app.ui_utils import apply_app_theme, render_brand_header, render_user_sidebar, require_auth, get_current_user
except ImportError:
    from ui_utils import apply_app_theme, render_brand_header, render_user_sidebar, require_auth, get_current_user

st.set_page_config(page_title="Admin Console | TREKVERSE", page_icon="🛡️", layout="wide")
apply_app_theme()
render_user_sidebar()

if not require_auth(allowed_roles=["admin"]):
    st.stop()

current_user = get_current_user()

render_brand_header(
    title="Institutional Governance & Administration Console",
    subtitle="User Access Control, Dataset Ingestion Studio, Model Version Registry, and Risk Governance"
)

tab_users, tab_import, tab_models, tab_settings, tab_audit = st.tabs([
    "👥 User Management",
    "📥 Data Import Studio",
    "🧠 Model Registry & Retraining",
    "⚙️ Risk Thresholds & Settings",
    "📜 System Audit Logs"
])

# 1. User Management
with tab_users:
    st.subheader("User Account Directory & Permissions")
    users = list_users()
    users_df = pd.DataFrame(users)
    st.dataframe(
        users_df[["id", "username", "full_name", "role", "email", "department", "status", "created_at"]],
        use_container_width=True,
        hide_index=True
    )

    with st.expander("➕ Register New Institutional User"):
        with st.form("create_user_form"):
            uc1, uc2 = st.columns(2)
            with uc1:
                new_uname = st.text_input("Username *")
                new_pwd = st.text_input("Temporary Password *", type="password")
                new_role = st.selectbox("Role *", ["faculty", "student", "admin"])
            with uc2:
                new_fname = st.text_input("Full Name *")
                new_email = st.text_input("Official Email *")
                new_dept = st.selectbox("Department *", ["Computer Science", "Information Technology", "Electronics", "Data Science", "Administration"])

            submitted = st.form_submit_button("Register User")
            if submitted:
                if not (new_uname and new_pwd and new_fname and new_email):
                    st.error("Please complete all required fields.")
                else:
                    try:
                        uid = create_user(new_uname, new_pwd, new_role, new_fname, new_email, new_dept)
                        log_audit(current_user["id"], "USER_REGISTERED", f"Created user {new_uname} ({new_role})")
                        st.success(f"User {new_uname} successfully created (ID: {uid})!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating user: {e}")

# 2. Data Import Studio
with tab_import:
    st.subheader("Institutional Dataset Ingestion & Validation Studio (Section 8)")
    st.markdown("""
    Upload semester records in **CSV** or **Excel (.xlsx)** format. 
    The studio performs automated schema mapping, range validation, duplicate checks, and shows row-level errors before commit.
    """)

    uploaded_file = st.file_uploader("Select institutional data file", type=["csv", "xlsx"])
    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                raw_df = pd.read_csv(uploaded_file)
            else:
                raw_df = pd.read_excel(uploaded_file)

            st.write(f"**Loaded Preview ({len(raw_df)} rows, {len(raw_df.columns)} columns):**")
            st.dataframe(raw_df.head(5), use_container_width=True)

            # Auto-detect Mapping
            auto_map = auto_detect_column_mapping(list(raw_df.columns))
            
            with st.expander("🛠️ Column Header Mapping Verification", expanded=True):
                st.caption("Match your institution's column headers with canonical application fields:")
                map_cols = st.columns(3)
                final_mapping = {}
                col_options = ["(None)"] + list(raw_df.columns)

                canon_fields = [
                    ("student_id", "Student ID *", 0),
                    ("name", "Full Name", 1),
                    ("department", "Department", 2),
                    ("semester", "Semester", 0),
                    ("attendance", "Attendance % *", 1),
                    ("previous_cgpa", "Previous CGPA *", 2),
                    ("internal_marks", "Internal Marks", 0),
                    ("assignment_marks", "Assignment Marks", 1),
                    ("study_hours", "Daily Study Hours", 2),
                    ("backlogs", "Backlogs Count", 0),
                    ("final_marks", "Final Marks (Target)", 1)
                ]

                for canon, label, col_idx in canon_fields:
                    default_choice = auto_map.get(canon, "(None)")
                    idx = col_options.index(default_choice) if default_choice in col_options else 0
                    with map_cols[col_idx]:
                        sel = st.selectbox(label, col_options, index=idx, key=f"map_{canon}")
                        if sel != "(None)":
                            final_mapping[canon] = sel

            # Validation button
            if st.button("Validate Dataset Against Integrity Rules", type="primary"):
                clean_df, errors, summary = validate_and_clean_data(raw_df, final_mapping)
                st.session_state["staging_clean_df"] = clean_df
                st.session_state["staging_errors"] = errors
                st.session_state["staging_summary"] = summary

            if "staging_summary" in st.session_state:
                sum_info = st.session_state["staging_summary"]
                errs = st.session_state["staging_errors"]
                c_clean = st.session_state["staging_clean_df"]

                vc1, vc2, vc3 = st.columns(3)
                vc1.metric("Total Rows", sum_info["total_rows"])
                vc2.metric("Valid Rows", sum_info["valid_rows"])
                vc3.metric("Rejected / Erroneous Rows", sum_info["rejected_rows"])

                if errs:
                    st.error(f"⚠️ Encountered {len(errs)} integrity issues. Invalid rows cannot be committed:")
                    err_df = pd.DataFrame(errs)
                    st.dataframe(err_df, use_container_width=True)

                if not c_clean.empty:
                    st.success(f"✅ {len(c_clean)} rows passed validation and are ready to commit.")
                    if st.button("Commit Validated Records to Database", type="primary"):
                        predictor = StudentPredictor()
                        committed = 0
                        for _, row in c_clean.iterrows():
                            upsert_student(dict(row))
                            committed += 1
                        log_audit(current_user["id"], "DATA_IMPORT", f"Committed {committed} student records from {uploaded_file.name}")
                        st.success(f"Successfully committed {committed} student records into database!")
                        del st.session_state["staging_summary"]
                        st.rerun()

        except Exception as e:
            st.error(f"Error processing file: {e}")

# 3. Model Registry & Retraining
with tab_models:
    st.subheader("Model Registry & Validation Metrics (Section 7)")
    meta_path = os.path.join(MODEL_REGISTRY_DIR, "model_metadata.json")
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        rc1, rc2, rc3 = st.columns(3)
        rc1.info(f"**Active Model Version:** `{meta.get('version')}`\n\n**Trained On:** {meta.get('training_date')}")
        rc2.success(f"**Selected Regressor:** {meta.get('selected_regressor')}\n\n**Evaluation Metric:** MAE & R² on Holdout")
        rc3.warning(f"**Selected Classifier:** {meta.get('selected_classifier')}\n\n**Evaluation Metric:** Macro F1 & ROC-AUC")

        st.markdown("#### Regression Candidates Comparison (Target: Predicted Score / 20)")
        reg_df = pd.DataFrame(meta.get("regression_comparison", {})).T
        st.dataframe(reg_df.style.highlight_max(subset=["R2", "CV_R2_Mean"], color="#D1FAE5").highlight_min(subset=["MAE", "RMSE"], color="#D1FAE5"), use_container_width=True)

        st.markdown("#### Risk Classification Candidates Comparison (Target: Risk Band)")
        clf_df = pd.DataFrame(meta.get("classification_comparison", {})).T
        if "Confusion_Matrix" in clf_df.columns:
            clf_df = clf_df.drop(columns=["Confusion_Matrix"])
        st.dataframe(clf_df.style.highlight_max(subset=["Accuracy", "F1_Macro", "ROC_AUC"], color="#D1FAE5"), use_container_width=True)

        st.markdown("#### Global Feature Importances")
        feat_imps = meta.get("feature_importances", {}).get("regressor", {})
        if feat_imps:
            f_df = pd.DataFrame(list(feat_imps.items()), columns=["Feature", "Importance"]).sort_values("Importance", ascending=False)
            st.bar_chart(f_df.set_index("Feature"))

        st.divider()
        if st.button("🔄 Retrain Models with Latest Database Records", type="secondary"):
            with st.spinner("Retraining candidate models, executing 5-fold cross-validation, and updating model registry..."):
                new_meta = train_and_evaluate_models()
                log_audit(current_user["id"], "MODEL_RETRAIN", f"Retrained models version {new_meta.get('version')}")
                st.success("Model registry updated successfully!")
                st.rerun()

# 4. Settings & Risk Thresholds
with tab_settings:
    st.subheader("Configurable Risk Thresholds & Institutional Policies (Section 3)")
    st.caption("Configure transparent early-warning thresholds agreed upon with academic leadership:")

    with st.form("settings_form"):
        sc1, sc2 = st.columns(2)
        with sc1:
            att_high = st.slider("High Risk Attendance Cutoff (%)", min_value=50.0, max_value=85.0, value=float(get_setting("high_risk_threshold_attendance", "75.0")), step=1.0)
            cgpa_high = st.slider("High Risk CGPA Cutoff", min_value=4.0, max_value=7.5, value=float(get_setting("high_risk_threshold_cgpa", "6.0")), step=0.1)
        with sc2:
            att_mod = st.slider("Moderate Risk Attendance Cutoff (%)", min_value=70.0, max_value=90.0, value=float(get_setting("moderate_risk_threshold_attendance", "80.0")), step=1.0)
            scale = st.selectbox("Score Output Scale", ["20.0", "100.0"], index=0 if get_setting("max_score_scale", "20.0") == "20.0" else 1)

        inst_name = st.text_input("Institution Name Banner", value=get_setting("institution_name", "TREKVERSE AI ACADEMY"))

        save_sett = st.form_submit_button("Save Policy Settings")
        if save_sett:
            set_setting("high_risk_threshold_attendance", str(att_high))
            set_setting("high_risk_threshold_cgpa", str(cgpa_high))
            set_setting("moderate_risk_threshold_attendance", str(att_mod))
            set_setting("max_score_scale", scale)
            set_setting("institution_name", inst_name)
            log_audit(current_user["id"], "SETTINGS_UPDATED", "Updated institutional risk thresholds and display scales.")
            st.success("System settings updated successfully!")
            st.rerun()

# 5. System Audit Logs
with tab_audit:
    st.subheader("Security & System Access Audit Logs (Section 9)")
    logs = get_recent_audit_logs(limit=100)
    if logs:
        l_df = pd.DataFrame(logs)
        st.dataframe(
            l_df[["id", "timestamp", "username", "role", "action", "details", "ip_address"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No audit entries recorded yet.")

