"""
Student segmentation and clustering module for TREKVERSE Student Success Platform.
Uses K-Means clustering to discover learning engagement personas with cautious academic interpretation.
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

MODEL_REGISTRY_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "models", "model_registry")

SEGMENT_PERSONAS = {
    0: {
        "title": "Consistent High Achievers",
        "description": "High attendance (>90%), top CGPA, consistent assignment submission, and strong LMS engagement.",
        "academic_interpretation": "Self-motivated cohort capable of peer mentoring, honors projects, or advanced research electives.",
        "recommended_action": "Provide enrichment challenges and leadership opportunities; continue baseline check-ins."
    },
    1: {
        "title": "Steady Balancers",
        "description": "Good attendance (80-90%), average to solid internal marks, steady submission rates.",
        "academic_interpretation": "Solid foundational understanding with steady progress. May benefit from targeted prep for challenging subjects.",
        "recommended_action": "Encourage structured weekly revision plans and subject-specific mock assessments."
    },
    2: {
        "title": "Attendance-Vulnerable",
        "description": "Moderate to strong marks, but declining attendance (often near or below the 75% regulatory barrier).",
        "academic_interpretation": "Demonstrates academic aptitude when present, but absenteeism risks regulatory exam detention and missed continuous evaluations.",
        "recommended_action": "Proactive advisor check-in to identify scheduling, health, or commute obstacles before exam qualification deadlines."
    },
    3: {
        "title": "Priority Support Cohort",
        "description": "Low attendance (<70%), previous backlogs, low assignment completion, and depressed assessment averages.",
        "academic_interpretation": "High multi-factor vulnerability requiring holistic faculty intervention and structured learning roadmaps.",
        "recommended_action": "Immediate faculty counselor outreach, remedial workshops, and structured weekly milestone plans."
    }
}

def train_student_clustering(df: pd.DataFrame, n_clusters: int = 4, seed: int = 42) -> Tuple[KMeans, StandardScaler, pd.DataFrame]:
    """Train K-Means clustering on student engagement and academic factors."""
    features = ["attendance", "previous_cgpa", "internal_marks", "assignment_marks", "study_hours", "backlogs"]
    X = df[features].copy()
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=seed, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)
    
    # Save artifacts
    os.makedirs(MODEL_REGISTRY_DIR, exist_ok=True)
    cluster_path = os.path.join(MODEL_REGISTRY_DIR, "kmeans_clusterer.joblib")
    joblib.dump({"model": kmeans, "scaler": scaler, "features": features, "personas": SEGMENT_PERSONAS}, cluster_path)
    
    res_df = df.copy()
    res_df["cluster"] = clusters
    res_df["persona_title"] = [SEGMENT_PERSONAS[c]["title"] for c in clusters]
    
    return kmeans, scaler, res_df

def predict_student_cluster(student_row: pd.Series) -> Dict[str, Any]:
    """Assign an individual student to an engagement persona with academic interpretation."""
    cluster_path = os.path.join(MODEL_REGISTRY_DIR, "kmeans_clusterer.joblib")
    if not os.path.exists(cluster_path):
        return SEGMENT_PERSONAS[1]
    
    artifact = joblib.load(cluster_path)
    kmeans = artifact["model"]
    scaler = artifact["scaler"]
    features = artifact["features"]
    
    vals = np.array([float(student_row.get(f, 0.0)) for f in features]).reshape(1, -1)
    vals_scaled = scaler.transform(vals)
    cluster_idx = int(kmeans.predict(vals_scaled)[0])
    
    persona = SEGMENT_PERSONAS.get(cluster_idx, SEGMENT_PERSONAS[1]).copy()
    persona["cluster_id"] = cluster_idx
    return persona

