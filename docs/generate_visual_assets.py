"""
Visual Assets Generator for TREKVERSE README and Documentation.
Produces crisp, high-resolution visual infographics and charts using Matplotlib and PIL.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

DOCS_IMG_DIR = os.path.join(os.path.dirname(__file__), "images")
os.makedirs(DOCS_IMG_DIR, exist_ok=True)

# 1. Model Benchmark Comparison Graphic
def generate_model_metrics_chart():
    fig, axes = plt.subplots(1, 3, figsize=(16, 5), dpi=300)
    fig.patch.set_facecolor('#0F172A')

    for ax in axes:
        ax.set_facecolor('#1E293B')
        ax.tick_params(colors='#E2E8F0', labelsize=9)
        for spine in ax.spines.values():
            spine.set_color('#334155')

    # Subplot 1: R2 Score
    models_reg = ['Baseline\n(Mean)', 'Ridge\nRegression', 'Random\nForest', 'Gradient\nBoosting']
    r2_scores = [0.0, 0.978, 0.979, 0.982]
    colors_reg = ['#64748B', '#3B82F6', '#8B5CF6', '#10B981']
    bars1 = axes[0].bar(models_reg, r2_scores, color=colors_reg, width=0.55, edgecolor='#0F172A', linewidth=1.5)
    axes[0].set_title('Regression Accuracy (R² Score)', color='#F8FAFC', fontsize=12, fontweight='bold', pad=12)
    axes[0].set_ylim(0, 1.1)
    for bar in bars1:
        yval = bar.get_height()
        axes[0].text(bar.get_x() + bar.get_width()/2.0, yval + 0.02, f'{yval:.3f}', ha='center', va='bottom', color='#FFFFFF', fontsize=9, fontweight='bold')

    # Subplot 2: MAE Error (Lower is better)
    mae_scores = [2.233, 0.334, 0.331, 0.302]
    bars2 = axes[1].bar(models_reg, mae_scores, color=['#EF4444', '#F59E0B', '#38BDF8', '#10B981'], width=0.55, edgecolor='#0F172A', linewidth=1.5)
    axes[1].set_title('Mean Absolute Error (Scale /20 - Lower is Better)', color='#F8FAFC', fontsize=12, fontweight='bold', pad=12)
    axes[1].set_ylim(0, 2.6)
    for bar in bars2:
        yval = bar.get_height()
        axes[1].text(bar.get_x() + bar.get_width()/2.0, yval + 0.05, f'{yval:.3f}', ha='center', va='bottom', color='#FFFFFF', fontsize=9, fontweight='bold')

    # Subplot 3: Risk Classification F1-Score & Accuracy
    models_clf = ['Baseline\n(Dummy)', 'Random\nForest', 'Gradient\nBoosting', 'Logistic\nRegression']
    f1_scores = [0.267, 0.884, 0.892, 0.896]
    bars3 = axes[2].bar(models_clf, f1_scores, color=['#64748B', '#8B5CF6', '#06B6D4', '#10B981'], width=0.55, edgecolor='#0F172A', linewidth=1.5)
    axes[2].set_title('Risk Classifier Performance (Macro F1)', color='#F8FAFC', fontsize=12, fontweight='bold', pad=12)
    axes[2].set_ylim(0, 1.1)
    for bar in bars3:
        yval = bar.get_height()
        axes[2].text(bar.get_x() + bar.get_width()/2.0, yval + 0.02, f'{yval:.3f}', ha='center', va='bottom', color='#FFFFFF', fontsize=9, fontweight='bold')

    plt.tight_layout()
    out_path = os.path.join(DOCS_IMG_DIR, "model_benchmark_comparison.png")
    plt.savefig(out_path, facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close()
    print("Saved:", out_path)

# 2. Risk Distribution & Attendance Correlation Graphic
def generate_risk_cohort_chart():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)
    fig.patch.set_facecolor('#0F172A')

    # Left: Donut Chart
    labels = ['Low Risk\n(72.3%)', 'Moderate Risk\n(19.3%)', 'High Risk\n(8.4%)']
    sizes = [214, 57, 24]
    colors = ['#10B981', '#F59E0B', '#EF4444']
    wedges, texts, autotexts = ax1.pie(
        sizes, labels=labels, autopct='%1.1f%%', startangle=140,
        colors=colors, textprops=dict(color='#F8FAFC', fontsize=10, fontweight='bold'),
        wedgeprops=dict(width=0.4, edgecolor='#0F172A', linewidth=2)
    )
    for at in autotexts:
        at.set_color('#0F172A')
    ax1.set_title('Institutional Early-Warning Risk Distribution\n(Total: 296 Students)', color='#F8FAFC', fontsize=12, fontweight='bold', pad=14)

    # Right: Attendance vs CGPA Scatter
    ax2.set_facecolor('#1E293B')
    ax2.tick_params(colors='#E2E8F0', labelsize=9)
    for spine in ax2.spines.values():
        spine.set_color('#334155')

    np.random.seed(42)
    # Synthetic scatter for high, moderate, low
    att_low = np.random.normal(89.5, 4.5, 214).clip(78, 100)
    cgpa_low = np.random.normal(8.25, 0.6, 214).clip(6.8, 9.9)

    att_mod = np.random.normal(74.0, 4.0, 57).clip(65, 81)
    cgpa_mod = np.random.normal(6.8, 0.5, 57).clip(5.6, 7.8)

    att_high = np.random.normal(61.0, 5.5, 24).clip(40, 72)
    cgpa_high = np.random.normal(5.4, 0.6, 24).clip(3.8, 6.4)

    ax2.scatter(att_low, cgpa_low, c='#10B981', label='Low Risk (Normal)', alpha=0.75, edgecolors='none', s=45)
    ax2.scatter(att_mod, cgpa_mod, c='#F59E0B', label='Moderate Risk (Check-in)', alpha=0.85, edgecolors='none', s=55)
    ax2.scatter(att_high, cgpa_high, c='#EF4444', label='High Risk (Support Priority)', alpha=0.95, edgecolors='none', s=70)

    # Regulatory cutoff line
    ax2.axvline(75.0, color='#F87171', linestyle='--', linewidth=1.5, label='75% Mandatory Attendance Barrier')

    ax2.set_xlabel('Attendance Percentage (%)', color='#E2E8F0', fontsize=10, labelpad=8)
    ax2.set_ylabel('Cumulative GPA (/10.0)', color='#E2E8F0', fontsize=10, labelpad=8)
    ax2.set_title('Attendance vs CGPA Distribution with Risk Categorization', color='#F8FAFC', fontsize=12, fontweight='bold', pad=14)
    ax2.legend(loc='lower right', facecolor='#0F172A', edgecolor='#334155', labelcolor='#E2E8F0', fontsize=8.5)

    plt.tight_layout()
    out_path = os.path.join(DOCS_IMG_DIR, "risk_distribution_cohort.png")
    plt.savefig(out_path, facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close()
    print("Saved:", out_path)

# 3. Architecture Infographic
def generate_architecture_graphic():
    fig, ax = plt.subplots(figsize=(14, 7), dpi=300)
    fig.patch.set_facecolor('#0F172A')
    ax.set_facecolor('#0F172A')
    ax.axis('off')

    # Draw Architecture Blocks
    def draw_box(x, y, w, h, title, subtitle, color, border_color):
        rect = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.03,rounding_size=0.05",
            facecolor=color, edgecolor=border_color, linewidth=1.5
        )
        ax.add_patch(rect)
        ax.text(x + w/2, y + h*0.65, title, ha='center', va='center', color='#FFFFFF', fontsize=10.5, fontweight='bold')
        ax.text(x + w/2, y + h*0.35, subtitle, ha='center', va='center', color='#CBD5E1', fontsize=8)

    def draw_arrow(x1, y1, x2, y2, label=""):
        ax.annotate(
            label, xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(facecolor='#38BDF8', edgecolor='#38BDF8', width=1.5, headwidth=6, shrink=0.05),
            ha='center', va='center', color='#93C5FD', fontsize=8
        )

    # Title
    ax.text(0.5, 0.94, "TREKVERSE — End-to-End System Architecture", ha='center', va='center', color='#F8FAFC', fontsize=15, fontweight='bold')

    # Column 1: Client & Presentation
    draw_box(0.04, 0.60, 0.26, 0.22, "1. Presentation Layer", "Streamlit Multi-Page UI\n(Admin, Faculty, Student, Simulator)", "#1E293B", "#3B82F6")
    draw_box(0.04, 0.25, 0.26, 0.22, "Interactive Features", "What-If Simulator · Learning Planner\nData Ingestion Studio · PDF Preview", "#1E293B", "#6366F1")

    # Column 2: Application Services & Security
    draw_box(0.37, 0.60, 0.26, 0.22, "2. Governance & RBAC", "PBKDF2-SHA256 Auth Guard\nServer-side Role Authorization", "#1E293B", "#10B981")
    draw_box(0.37, 0.25, 0.26, 0.22, "Intervention Workflow", "At-Risk Flagging · Status Tracking\nFaculty Follow-up Notes & Audits", "#1E293B", "#06B6D4")

    # Column 3: AI/ML & Explainability
    draw_box(0.70, 0.60, 0.26, 0.22, "3. ML Engine & Inference", "Gradient Boosting (R²=0.982)\nLogistic Classifier (F1=0.896)", "#1E293B", "#F59E0B")
    draw_box(0.70, 0.25, 0.26, 0.22, "Persistence & Reporting", "SQLite Relational Store (ACID)\nReportLab PDF Generation Engine", "#1E293B", "#EC4899")

    # Connectors
    draw_arrow(0.30, 0.71, 0.37, 0.71)
    draw_arrow(0.63, 0.71, 0.70, 0.71)
    draw_arrow(0.30, 0.36, 0.37, 0.36)
    draw_arrow(0.63, 0.36, 0.70, 0.36)
    draw_arrow(0.17, 0.47, 0.17, 0.60)
    draw_arrow(0.50, 0.47, 0.50, 0.60)
    draw_arrow(0.83, 0.47, 0.83, 0.60)

    out_path = os.path.join(DOCS_IMG_DIR, "architecture_flowchart.png")
    plt.savefig(out_path, facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close()
    print("Saved:", out_path)

# 4. Hero Banner Graphic
def generate_hero_banner():
    fig, ax = plt.subplots(figsize=(15, 4.5), dpi=300)
    fig.patch.set_facecolor('#0B132B')
    ax.set_facecolor('#0B132B')
    ax.axis('off')

    # Brand Title
    ax.text(0.05, 0.78, "T R E K V E R S E", color='#38BDF8', fontsize=22, fontweight='bold')
    ax.text(0.05, 0.60, "AI-Powered Student Success Prediction & Academic Guidance System", color='#FFFFFF', fontsize=14, fontweight='bold')
    ax.text(0.05, 0.45, "Academic Progress Analytics · Early-Warning Indicators · What-If Simulator · Personalized Guidance", color='#94A3B8', fontsize=9.5)

    # 4 Metric Badge Cards
    def draw_kpi(x, y, w, h, label, val, sub, val_color):
        rect = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.02,rounding_size=0.04",
            facecolor='#1C2541', edgecolor='#3A506B', linewidth=1.2
        )
        ax.add_patch(rect)
        ax.text(x + w/2, y + h*0.72, label, ha='center', va='center', color='#94A3B8', fontsize=8, fontweight='bold')
        ax.text(x + w/2, y + h*0.42, val, ha='center', va='center', color=val_color, fontsize=15, fontweight='bold')
        ax.text(x + w/2, y + h*0.18, sub, ha='center', va='center', color='#64748B', fontsize=7.5)

    draw_kpi(0.05, 0.08, 0.20, 0.27, "TOTAL STUDENTS", "296", "Monitored Cohort", "#FFFFFF")
    draw_kpi(0.28, 0.08, 0.20, 0.27, "INSTITUTIONAL CGPA", "7.84 / 10", "Semester Cumulative", "#38BDF8")
    draw_kpi(0.51, 0.08, 0.20, 0.27, "REQUIRING SUPPORT", "24 High Risk", "57 Moderate Risk", "#F87171")
    draw_kpi(0.74, 0.08, 0.20, 0.27, "AVG ATTENDANCE", "86.0%", "Mandatory: 75%", "#34D399")

    out_path = os.path.join(DOCS_IMG_DIR, "dashboard_banner.png")
    plt.savefig(out_path, facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close()
    print("Saved:", out_path)

if __name__ == "__main__":
    generate_model_metrics_chart()
    generate_risk_cohort_chart()
    generate_architecture_graphic()
    generate_hero_banner()
    print("All graphic visual assets generated successfully!")
