# TREKVERSE — AI-Powered Student Success Prediction & Academic Guidance System

A practical, explainable, data-backed student success platform engineered for higher education institutions. Rather than predicting only a final grade, the platform combines academic forecasting, progress monitoring, early-warning indicators, explainable predictions, engagement analysis, personalized learning guidance, role-based dashboards, and downloadable PDF reports.

> **Responsible AI Notice:** Student predictions provide timely, data-backed decision support for academic advisors and students. They do not replace faculty judgment and must not serve as the sole criterion for progression, grading, or academic penalties.

---

## 🚀 Key Target Capabilities

- **Monitor:** Tracks continuous attendance rates, attendance trends, continuous assessment marks, subject-level performance, and learning engagement.
- **Predict:** Estimates academic outcomes (scaled score out of 20 or 100) and identifies students requiring timely academic support via multi-tier risk classification.
- **Explain:** Unpacks the factors influencing every prediction through feature contribution decomposition and SHAP-aligned attribution (top positive accelerators and negative risk drivers).
- **Guide:** Dynamically generates actionable weekly study schedules (**AI-Personalized Learning Planner**) with interactive task completion tracking based on student weak areas.
- **Manage:** Role-based access control and experiences for **Administrator**, **Faculty**, and **Student** with server-side authorization enforcement.
- **Simulate:** Interactive **What-If Student Success Simulator** allowing students and faculty to simulate behavioral improvements (e.g. attendance, study hours, assignments) without modifying original records.
- **Report:** Generates and exports downloadable, publication-grade **PDF Student Success & Academic Guidance Reports** using ReportLab.

---

## 🏛️ System Architecture & Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend / Web UI** | Streamlit, Custom Responsive CSS (Inter typography, Trekverse Navy/Slate design system), Plotly Express & Graph Objects |
| **Machine Learning Engine** | Python, scikit-learn (Random Forest, Gradient Boosting, Ridge, Logistic Regression, K-Means Clustering, StandardScaler) |
| **Explainability** | Tree Feature Contribution Decomposition & SHAP-aligned factor attribution |
| **Database & Persistence** | SQLite relational database with ACID transactions, PBKDF2-SHA256 password security, and foreign key integrity |
| **PDF Reporting** | ReportLab (tabular layouts, dynamic risk badges, disclaimers, executive styling) |
| **Data Ingestion Studio** | Automated column mapping, type inference, range checks, and row-level error reporting (CSV / XLSX) |
| **Testing** | pytest test suite covering database transactions, ML pipeline, simulator deltas, and PDF generation |

---

## 📂 Project Structure

```
AI-Powered-Student-Success/
├── app/
│   ├── app.py                     # Main application entrypoint, authentication, and KPI overview
│   ├── ui_utils.py                # Cohesive theme styles, navbar guards, brand banners
│   └── pages/
│       ├── admin.py               # Administrator Dashboard: User management, data import studio, model registry & system logs
│       ├── faculty.py             # Faculty Dashboard: At-risk student queue, diagnostic view, intervention tracker
│       ├── student.py             # Student Dashboard: Academic profile, AI-personalized weekly planner, report download
│       ├── analytics.py           # Deep Learning Analytics: Cohort distributions, scatter plots, K-Means personas
│       ├── prediction.py          # What-If Student Success Simulator: Scenario adjustments vs baseline comparison
│       └── reports.py             # Automatic PDF Student Success Report generator & instant preview
├── data/
│   ├── raw/
│   │   └── student_academic_records.csv   # Calibrated benchmark dataset (296 students across departments)
│   ├── processed/
│   └── uploads/
├── models/
│   ├── model_registry/
│   │   ├── student_performance_regressor.joblib   # Trained Gradient Boosting Regressor (R² = 0.982)
│   │   ├── student_risk_classifier.joblib        # Trained Classifier (Accuracy = 96.7%, Macro F1 = 0.896)
│   │   ├── kmeans_clusterer.joblib               # K-Means Student Segmentation Model (k=4)
│   │   └── model_metadata.json                   # Complete model evaluation metrics and documentation
│   └── preprocessor/
│       └── scaler_pipeline.joblib                # Feature scaler and column definitions
├── src/
│   ├── preprocessing/
│   │   └── data_cleaner.py        # Schema checks, range validation, missing value imputation
│   ├── feature_engineering/
│   │   └── feature_pipeline.py    # Attendance deficit, backlog severity, assessment ratios, engagement index
│   ├── training/
│   │   └── model_trainer.py       # Benchmark generation, 5-fold cross-validation, candidate evaluation
│   ├── prediction/
│   │   └── predictor.py           # Real-time inference service, subject-wise forecasts, what-if simulator
│   ├── explainability/
│   │   └── explainer.py           # Feature attribution, positive accelerators and vulnerability drivers
│   ├── recommendations/
│   │   └── recommender.py         # Personalized study recommendations and weekly schedule generator
│   └── clustering/
│       └── student_segmentation.py# Unsupervised student personas with cautious academic interpretation
├── database/
│   ├── schema.sql                 # Relational schema (11 entities: users, students, subjects, marks, predictions, interventions, study_plans, etc.)
│   ├── database.py                # SQLite connection, CRUD methods, security hashing, audit logs
│   ├── seed_data.py               # Database seeder (296 students, initial models, sample faculty interventions)
│   └── student_success.db         # Persistent SQLite database
├── reports/
│   ├── report_generator.py        # ReportLab PDF generator matching Section 10 layout
│   └── sample_STU1024.pdf         # Sample verified generated PDF report
├── tests/
│   ├── test_database.py           # Pytest tests for schema, authentication, CRUD, and study plan toggles
│   ├── test_pipeline.py           # Pytest tests for validation, feature engineering, prediction, and simulator
│   └── test_reports.py            # Pytest tests for ReportLab PDF binary generation
├── run_app.bat                    # One-click Windows launcher
├── requirements.txt               # Python package dependencies
└── README.md                      # Comprehensive project documentation
```

---

## 👥 Default Demo Credentials

The platform is pre-seeded with role-based user accounts for testing:

| Role | Username | Password | Full Name / Description |
|---|---|---|---|
| **Administrator** | `admin` | `admin123` | Institutional Administrator (Full system & data governance) |
| **Faculty Advisor** | `prof_sharma` | `faculty123` | Prof. R. Sharma (HOD Computer Science) |
| **Faculty Advisor** | `prof_rao` | `faculty123` | Dr. Anita Rao (Data Science & AI) |
| **Student (Moderate Risk)** | `stu1024` | `student123` | Kavya Deshmukh (STU1024, CS Sem 5, Att: 68%, 1 Backlog) |
| **Student (High Performer)** | `stu1000` | `student123` | Aarav Sharma (STU1000, CS Sem 5, Att: 94%, CGPA: 8.9) |
| **Student (High Risk)** | `stu1050` | `student123` | Devansh Joshi (STU1050, ECE Sem 4, Att: 58%, 2 Backlogs) |

*You can also use the one-click quick login buttons directly on the home page.*

---

## 🛠️ Installation & Quick Start

### 1. Requirements
Ensure Python 3.10+ is installed on your system.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Re-seed Database & Retrain Models (Optional)
```bash
python database/seed_data.py
```

### 4. Launch the Web Application
Run the launcher batch file:
```bash
run_app.bat
```
Or start Streamlit directly:
```bash
streamlit run app/app.py
```
Open your browser at `http://localhost:8501`.

### 5. Run Unit Test Suite
```bash
pytest tests -v
```

---

## 📊 Model Evaluation Summary

Trained on 296 institutional benchmark records with an 80/20 stratified holdout split and 5-fold cross-validation:

### Regression (Target: Predicted Score / 20.0)
- **Baseline (Mean Regressor):** $R^2 = 0.000$, MAE = 2.23 pts
- **Ridge Regression:** $R^2 = 0.978$, MAE = 0.33 pts
- **Random Forest Regressor:** $R^2 = 0.979$, MAE = 0.33 pts
- **Selected Model — Gradient Boosting:** **$R^2 = 0.982$**, **MAE = 0.30 pts**, **RMSE = 0.38 pts**

### Classification (Target: Risk Band — Low, Moderate, High)
- **Baseline (Most Frequent):** Accuracy = 66.7%, Macro F1 = 0.267
- **Selected Model — Logistic Regression / Random Forest:** **Accuracy = 96.7%**, **Macro F1 = 0.896**, **ROC-AUC = 0.995**

---

## 📜 Compliance with Proposal Sections

1. **Section 1 & 2 (Capabilities):** Combines academic forecasting, progress monitoring, early-warning indicators, explainable predictions, engagement analysis, personalized learning guidance, role-based dashboards, and downloadable reports.
2. **Section 3 (Monitoring & Risk Bands):** Three transparent risk levels (Low, Moderate, High) calculated from attendance, CGPA, backlogs, and continuous assessments.
3. **Section 4 (What-If Simulator):** Live simulator allowing slider adjustments (attendance, study hours, assignments) with baseline vs scenario comparison and score delta; keeps original student records unchanged.
4. **Section 5 (Role-Based Dashboards):** Specialized views for Admin, Faculty, and Student with server-side authorization checks.
5. **Section 6 (Subject-Wise Prediction):** Subject-level forecasts for Mathematics, Programming, DBMS, Computer Networks, and Electronics with actionable interpretations.
6. **Section 7 (ML Pipeline):** Schema checks, holdout validation, baseline comparison, metrics reporting (MAE, RMSE, R², Accuracy, F1, ROC-AUC), and model registry persistence.
7. **Section 8 (Data Import Studio):** Ingestion interface for CSV/Excel with column mapping, range validation, and row-level error reporting before commit.
8. **Section 9 (Database Architecture):** Relational schema spanning users, students, subjects, attendance, marks, predictions, interventions, and audit logs.
9. **Section 10 (PDF Reports):** Publication-grade ReportLab PDF generation with Header, Demographics, AI Analysis, Subject breakdown, Guidance, Remarks, and Disclaimer.
10. **Section 11 (Learning Planner & Personas):** Weekly study schedule with interactive task completion tracking + K-Means student clustering with cautious academic interpretations.

