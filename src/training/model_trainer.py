"""
Machine Learning training and model comparison pipeline for TREKVERSE Student Success Platform.
Evaluates baseline vs ensemble models (Random Forest, Gradient Boosting, Ridge, Logistic Regression),
validates on holdout test set with 5-fold cross-validation, and persists versioned models to the model registry.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple

from sklearn.model_selection import train_test_split, KFold, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.dummy import DummyRegressor, DummyClassifier
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.ensemble import (
    RandomForestRegressor, GradientBoostingRegressor,
    RandomForestClassifier, GradientBoostingClassifier
)
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, roc_auc_score
)

from src.feature_engineering.feature_pipeline import FEATURE_COLUMNS, engineer_features, calculate_heuristic_risk

MODEL_REGISTRY_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "models", "model_registry")
PREPROCESSOR_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "models", "preprocessor")
DATA_RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw")

def generate_benchmark_dataset(n_samples: int = 296, seed: int = 42) -> pd.DataFrame:
    """
    Generates a realistic academic dataset calibrated to institution benchmarks:
    ~296 students, class avg CGPA ~7.84, attendance ~86%, balanced distribution of risk.
    """
    np.random.seed(seed)
    
    departments = ["Computer Science", "Information Technology", "Electronics", "Data Science"]
    student_ids = [f"STU{1000 + i}" for i in range(n_samples)]
    names = [
        "Aarav Sharma", "Aditi Patel", "Ananya Rao", "Arjun Reddy", "Bhavna Nair",
        "Chirag Gupta", "Deepika Iyer", "Devansh Joshi", "Divya Menon", "Gaurav Verma",
        "Ishaan Pillai", "Kavya Deshmukh", "Kiran Kulkarni", "Manish Pandey", "Meera Sen",
        "Neha Nambiar", "Nikhil Bhat", "Pooja Hegde", "Pranav Varma", "Priya Das",
        "Rahul Saxena", "Riya Sen", "Rohan Mehta", "Sanjay Kumar", "Sneha Rao",
        "Siddharth Roy", "Tanvi Kapoor", "Varun Chauhan", "Vidya Krishnan", "Yash Malhotra"
    ]
    full_names = [f"{names[i % len(names)]} {1 + i // len(names)}" for i in range(n_samples)]
    depts = [departments[i % len(departments)] for i in range(n_samples)]
    semesters = np.random.choice([3, 4, 5, 6, 7], size=n_samples, p=[0.2, 0.2, 0.3, 0.2, 0.1])

    risk_assignment = np.random.choice(["Low", "Moderate", "High"], size=n_samples, p=[0.723, 0.193, 0.084])

    attendance = []
    cgpa = []
    backlogs = []
    internal_marks = []
    assignment_marks = []
    study_hours = []
    activity_score = []
    attendance_trend = []

    for r in risk_assignment:
        if r == "Low":
            att = np.clip(np.random.normal(89.5, 5.0), 78.0, 99.5)
            c = np.clip(np.random.normal(8.25, 0.7), 6.8, 9.9)
            bl = 0 if np.random.rand() > 0.05 else 1
            im = np.clip(c * 9.2 + np.random.normal(0, 3), 65.0, 98.0)
            am = np.clip(att * 0.9 + np.random.normal(5, 4), 70.0, 100.0)
            sh = np.clip(np.random.normal(3.8, 1.0), 1.5, 7.0)
            act = np.clip(np.random.normal(85.0, 8.0), 65.0, 100.0)
            trend = np.clip(np.random.normal(1.2, 2.5), -5.0, 8.0)
        elif r == "Moderate":
            att = np.clip(np.random.normal(74.0, 4.5), 65.0, 81.0)
            c = np.clip(np.random.normal(6.8, 0.6), 5.6, 7.8)
            bl = np.random.choice([0, 1, 2], p=[0.4, 0.45, 0.15])
            im = np.clip(c * 8.8 + np.random.normal(-3, 4), 48.0, 78.0)
            am = np.clip(att * 0.85 + np.random.normal(-2, 5), 55.0, 85.0)
            sh = np.clip(np.random.normal(2.4, 0.8), 1.0, 4.5)
            act = np.clip(np.random.normal(68.0, 9.0), 45.0, 85.0)
            trend = np.clip(np.random.normal(-1.5, 3.0), -10.0, 5.0)
        else: # High Risk
            att = np.clip(np.random.normal(61.0, 6.0), 40.0, 72.0)
            c = np.clip(np.random.normal(5.4, 0.7), 3.8, 6.4)
            bl = np.random.choice([1, 2, 3, 4], p=[0.3, 0.4, 0.2, 0.1])
            im = np.clip(c * 8.0 + np.random.normal(-6, 5), 35.0, 62.0)
            am = np.clip(att * 0.8 + np.random.normal(-6, 6), 38.0, 70.0)
            sh = np.clip(np.random.normal(1.5, 0.6), 0.5, 3.0)
            act = np.clip(np.random.normal(48.0, 10.0), 20.0, 65.0)
            trend = np.clip(np.random.normal(-4.5, 3.5), -15.0, 2.0)

        attendance.append(round(float(att), 1))
        cgpa.append(round(float(c), 2))
        backlogs.append(int(bl))
        internal_marks.append(round(float(im), 1))
        assignment_marks.append(round(float(am), 1))
        study_hours.append(round(float(sh), 1))
        activity_score.append(round(float(act), 1))
        attendance_trend.append(round(float(trend), 1))

    final_marks_20 = []
    risk_labels = []

    for i in range(n_samples):
        score_100 = (
            0.38 * internal_marks[i] +
            0.32 * (cgpa[i] * 10.0) +
            0.15 * attendance[i] +
            0.10 * assignment_marks[i] +
            0.05 * (study_hours[i] * 12.0) -
            3.0 * backlogs[i] +
            np.random.normal(0, 2.2)
        )
        score_20 = np.clip(score_100 / 5.0, 5.0, 19.8)
        final_marks_20.append(round(float(score_20), 1))
        
        band, _ = calculate_heuristic_risk(pd.Series({
            "attendance": attendance[i],
            "previous_cgpa": cgpa[i],
            "backlogs": backlogs[i],
            "internal_marks": internal_marks[i]
        }))
        risk_labels.append(band)

    df = pd.DataFrame({
        "student_id": student_ids,
        "name": full_names,
        "department": depts,
        "semester": semesters,
        "attendance": attendance,
        "attendance_trend": attendance_trend,
        "previous_cgpa": cgpa,
        "internal_marks": internal_marks,
        "assignment_marks": assignment_marks,
        "study_hours": study_hours,
        "backlogs": backlogs,
        "activity_score": activity_score,
        "final_marks": final_marks_20,
        "risk_band": risk_labels
    })

    return df

def train_and_evaluate_models() -> Dict[str, Any]:
    """Train candidate regression and classification models, compare metrics, and register best models."""
    os.makedirs(MODEL_REGISTRY_DIR, exist_ok=True)
    os.makedirs(PREPROCESSOR_DIR, exist_ok=True)
    os.makedirs(DATA_RAW_DIR, exist_ok=True)

    raw_path = os.path.join(DATA_RAW_DIR, "student_academic_records.csv")
    df = generate_benchmark_dataset(n_samples=296, seed=42)
    df.to_csv(raw_path, index=False)

    feat_df = engineer_features(df)
    X = feat_df[FEATURE_COLUMNS]
    y_reg = feat_df["final_marks"]
    y_clf = feat_df["risk_band"]

    band_to_int = {"Low Risk": 0, "Moderate Risk": 1, "High Risk": 2}
    int_to_band = {v: k for k, v in band_to_int.items()}
    y_clf_int = y_clf.map(band_to_int)

    X_train, X_test, y_reg_train, y_reg_test, y_clf_train, y_clf_test = train_test_split(
        X, y_reg, y_clf_int, test_size=0.20, random_state=42, stratify=y_clf_int
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    scaler_path = os.path.join(PREPROCESSOR_DIR, "scaler_pipeline.joblib")
    joblib.dump({"scaler": scaler, "feature_columns": FEATURE_COLUMNS}, scaler_path)

    # Candidate Regressors
    reg_candidates = {
        "Baseline (Mean)": DummyRegressor(strategy="mean"),
        "Ridge Regression": Ridge(alpha=1.0),
        "Random Forest": RandomForestRegressor(n_estimators=60, max_depth=6, random_state=42),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=60, max_depth=4, learning_rate=0.08, random_state=42)
    }

    reg_metrics = {}
    best_reg_name = None
    best_reg_r2 = -999.0
    best_reg_model = None

    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    for name, model in reg_candidates.items():
        if name in ["Ridge Regression", "Baseline (Mean)"]:
            model.fit(X_train_scaled, y_reg_train)
            preds = model.predict(X_test_scaled)
            cv_scores = cross_val_score(model, X_train_scaled, y_reg_train, cv=kf, scoring="r2")
        else:
            model.fit(X_train, y_reg_train)
            preds = model.predict(X_test)
            cv_scores = cross_val_score(model, X_train, y_reg_train, cv=kf, scoring="r2")

        mae = mean_absolute_error(y_reg_test, preds)
        rmse = np.sqrt(mean_squared_error(y_reg_test, preds))
        r2 = r2_score(y_reg_test, preds)

        reg_metrics[name] = {
            "MAE": round(float(mae), 3),
            "RMSE": round(float(rmse), 3),
            "R2": round(float(r2), 3),
            "CV_R2_Mean": round(float(np.mean(cv_scores)), 3),
            "CV_R2_Std": round(float(np.std(cv_scores)), 3)
        }

        if r2 > best_reg_r2:
            best_reg_r2 = r2
            best_reg_name = name
            best_reg_model = model

    # Candidate Classifiers
    clf_candidates = {
        "Baseline (Most Frequent)": DummyClassifier(strategy="most_frequent"),
        "Logistic Regression": LogisticRegression(max_iter=500, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=60, max_depth=6, random_state=42),
        "Gradient Boosting": GradientBoostingClassifier(n_estimators=60, max_depth=4, learning_rate=0.08, random_state=42)
    }

    clf_metrics = {}
    best_clf_name = None
    best_clf_f1 = -1.0
    best_clf_model = None

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    for name, model in clf_candidates.items():
        if name in ["Logistic Regression"]:
            model.fit(X_train_scaled, y_clf_train)
            preds = model.predict(X_test_scaled)
            probs = model.predict_proba(X_test_scaled)
            cv_scores = cross_val_score(model, X_train_scaled, y_clf_train, cv=skf, scoring="f1_macro")
        else:
            model.fit(X_train, y_clf_train)
            preds = model.predict(X_test)
            probs = model.predict_proba(X_test)
            cv_scores = cross_val_score(model, X_train, y_clf_train, cv=skf, scoring="f1_macro")

        acc = accuracy_score(y_clf_test, preds)
        prec = precision_score(y_clf_test, preds, average="weighted", zero_division=0)
        rec = recall_score(y_clf_test, preds, average="weighted", zero_division=0)
        f1 = f1_score(y_clf_test, preds, average="weighted", zero_division=0)
        f1_macro = f1_score(y_clf_test, preds, average="macro", zero_division=0)
        cm = confusion_matrix(y_clf_test, preds).tolist()
        
        try:
            auc = roc_auc_score(y_clf_test, probs, multi_class="ovr")
        except Exception:
            auc = 0.5

        clf_metrics[name] = {
            "Accuracy": round(float(acc), 3),
            "Precision": round(float(prec), 3),
            "Recall": round(float(rec), 3),
            "F1_Weighted": round(float(f1), 3),
            "F1_Macro": round(float(f1_macro), 3),
            "ROC_AUC": round(float(auc), 3),
            "CV_F1_Mean": round(float(np.mean(cv_scores)), 3),
            "Confusion_Matrix": cm
        }

        if f1_macro > best_clf_f1:
            best_clf_f1 = f1_macro
            best_clf_name = name
            best_clf_model = model

    reg_path = os.path.join(MODEL_REGISTRY_DIR, "student_performance_regressor.joblib")
    clf_path = os.path.join(MODEL_REGISTRY_DIR, "student_risk_classifier.joblib")
    joblib.dump(best_reg_model, reg_path)
    joblib.dump(best_clf_model, clf_path)

    feature_importances = {}
    if hasattr(best_reg_model, "feature_importances_"):
        feature_importances["regressor"] = {
            col: round(float(imp), 4)
            for col, imp in zip(FEATURE_COLUMNS, best_reg_model.feature_importances_)
        }
    if hasattr(best_clf_model, "feature_importances_"):
        feature_importances["classifier"] = {
            col: round(float(imp), 4)
            for col, imp in zip(FEATURE_COLUMNS, best_clf_model.feature_importances_)
        }

    metadata = {
        "version": "v1.0.0-ensemble",
        "training_date": "2026-11-23",
        "dataset_samples": len(df),
        "test_holdout_samples": len(X_test),
        "feature_columns": FEATURE_COLUMNS,
        "selected_regressor": best_reg_name,
        "selected_classifier": best_clf_name,
        "regression_comparison": reg_metrics,
        "classification_comparison": clf_metrics,
        "feature_importances": feature_importances,
        "label_mapping": int_to_band,
        "disclaimer": "Model outputs provide estimate support for early guidance; they must not replace qualified academic evaluation."
    }

    metadata_path = os.path.join(MODEL_REGISTRY_DIR, "model_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return metadata

if __name__ == "__main__":
    meta = train_and_evaluate_models()
    print("Model training complete!")
    print(f"Selected Regressor: {meta['selected_regressor']}")
    print(f"Selected Classifier: {meta['selected_classifier']}")
