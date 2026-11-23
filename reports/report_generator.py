"""
PDF Report Generator for TREKVERSE Student Success Platform.
Generates an official Student Success & Academic Guidance Report matching Section 10.
"""

import os
import io
from datetime import datetime
from typing import Dict, Any, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)

def generate_student_pdf_report(
    student_data: Dict[str, Any],
    prediction_data: Dict[str, Any],
    subject_scores: Optional[List[Dict[str, Any]]] = None,
    recommendations: Optional[List[Dict[str, Any]]] = None,
    faculty_remarks: Optional[str] = None,
    output_path: Optional[str] = None
) -> bytes:
    """
    Builds a professional PDF report containing student demographics, academic metrics,
    AI prediction & risk explanation, subject breakdown, personalized guidance, and official disclaimer.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer if not output_path else output_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1E3A8A"),
        alignment=0
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748B"),
        alignment=0
    )
    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=10,
        spaceAfter=4
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155")
    )
    body_bold = ParagraphStyle(
        "BodyDarkBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1E293B")
    )
    badge_style = ParagraphStyle(
        "BadgeText",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.white,
        alignment=1
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#475569")
    )

    story = []

    # 1. Header Banner
    header_table = Table(
        [
            [
                Paragraph("<b>TREKVERSE AI ACADEMY</b><br/><font size=12 color='#1E3A8A'>Student Success & Academic Guidance Report</font>", title_style),
                Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}<br/><b>Model:</b> {prediction_data.get('model_version', 'v1.0.0-ensemble')}<br/><b>Status:</b> Official Evaluation", subtitle_style)
            ]
        ],
        colWidths=[4.2 * inch, 3.0 * inch]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT')
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1E3A8A"), spaceBefore=2, spaceAfter=10))

    # 2. Student Demographics & Profile Table
    story.append(Paragraph("Student Academic Profile", h2_style))
    demo_data = [
        [
            Paragraph("<b>Student ID:</b>", body_style), Paragraph(str(student_data.get("student_id", "N/A")), body_bold),
            Paragraph("<b>Full Name:</b>", body_style), Paragraph(str(student_data.get("name", "Authorized Student")), body_bold)
        ],
        [
            Paragraph("<b>Department:</b>", body_style), Paragraph(str(student_data.get("department", "N/A")), body_bold),
            Paragraph("<b>Current Semester:</b>", body_style), Paragraph(f"Semester {student_data.get('semester', 'N/A')}", body_bold)
        ],
        [
            Paragraph("<b>Cumulative GPA:</b>", body_style), Paragraph(f"{student_data.get('cgpa', 0.0):.2f} / 10.0", body_bold),
            Paragraph("<b>Current Attendance:</b>", body_style), Paragraph(f"{student_data.get('attendance', 0.0):.1f}%", body_bold)
        ],
        [
            Paragraph("<b>Active Backlogs:</b>", body_style), Paragraph(str(student_data.get("backlogs", 0)), body_bold),
            Paragraph("<b>Self-Study Commitment:</b>", body_style), Paragraph(f"{student_data.get('study_hours', 2.0):.1f} hrs/day", body_bold)
        ]
    ]
    t_demo = Table(demo_data, colWidths=[1.8 * inch, 1.8 * inch, 1.8 * inch, 1.8 * inch])
    t_demo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_demo)
    story.append(Spacer(1, 12))

    # 3. AI Predictive Analysis & Risk Band
    story.append(Paragraph("AI Academic Forecasting & Early-Warning Analysis", h2_style))
    
    risk_band = prediction_data.get("risk_band", "Low Risk")
    band_color = colors.HexColor("#10B981") # Green
    if risk_band == "Moderate Risk":
        band_color = colors.HexColor("#F59E0B") # Amber
    elif risk_band == "High Risk":
        band_color = colors.HexColor("#EF4444") # Red

    ai_table_data = [
        [
            Paragraph("<b>Predicted Assessment Score:</b>", body_style),
            Paragraph(f"<font size=14 color='#1E3A8A'><b>{prediction_data.get('predicted_score', 0.0)}</b></font> / {prediction_data.get('predicted_scale', 20.0)}", body_style),
            Paragraph("<b>Early-Warning Risk Band:</b>", body_style),
            Table([[Paragraph(risk_band.upper(), badge_style)]], colWidths=[1.6 * inch], style=[
                ('BACKGROUND', (0, 0), (-1, -1), band_color),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ])
        ]
    ]
    t_ai = Table(ai_table_data, colWidths=[2.2 * inch, 1.4 * inch, 2.0 * inch, 1.6 * inch])
    t_ai.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
        ('BOX', (0, 0), (-1, -1), 1.0, colors.HexColor("#BFDBFE")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_ai)
    story.append(Spacer(1, 8))

    # Contributing Factors
    explanation = prediction_data.get("explanation", {})
    pos_factors = explanation.get("top_positive", [])
    neg_factors = explanation.get("top_negative", [])

    factor_rows = [[Paragraph("<b>Key Supporting Indicators (+)</b>", body_bold), Paragraph("<b>Key Risk Drivers (-)</b>", body_bold)]]
    max_len = max(len(pos_factors), len(neg_factors), 1)
    for i in range(max_len):
        pos_txt = f"+ {pos_factors[i]['description']}" if i < len(pos_factors) else "— Consistent engagement metrics"
        neg_txt = f"- {neg_factors[i]['description']}" if i < len(neg_factors) else "— No critical deficit identified"
        factor_rows.append([
            Paragraph(f"<font color='#065F46'>{pos_txt}</font>", body_style),
            Paragraph(f"<font color='#991B1B'>{neg_txt}</font>", body_style)
        ])

    t_factors = Table(factor_rows, colWidths=[3.6 * inch, 3.6 * inch])
    t_factors.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_factors)
    story.append(Spacer(1, 12))

    # 4. Subject-Wise Analytics Table
    if subject_scores:
        story.append(Paragraph("Subject-Wise Forecast & Diagnostic Interpretation", h2_style))
        subj_table_data = [
            [
                Paragraph("<b>Subject Course</b>", body_bold),
                Paragraph("<b>Predicted Score (/20)</b>", body_bold),
                Paragraph("<b>Academic Interpretation</b>", body_bold)
            ]
        ]
        for s in subject_scores:
            subj_table_data.append([
                Paragraph(s["subject"], body_style),
                Paragraph(f"{s['predicted_score']:.1f}", body_style),
                Paragraph(f"<b>{s['interpretation']}</b>", body_style)
            ])
        t_subj = Table(subj_table_data, colWidths=[3.0 * inch, 1.8 * inch, 2.4 * inch])
        t_subj.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t_subj)
        story.append(Spacer(1, 12))

    # 5. Personalized Recommendations & Faculty Follow-Up Plan
    story.append(Paragraph("Personalized Learning Guidance & Actionable Recommendations", h2_style))
    if recommendations:
        rec_table_data = [[Paragraph("<b>Priority</b>", body_bold), Paragraph("<b>Category</b>", body_bold), Paragraph("<b>Actionable Guidance</b>", body_bold)]]
        for r in recommendations[:4]:
            p_color = "#DC2626" if r.get("priority") == "High" else "#D97706"
            rec_table_data.append([
                Paragraph(f"<font color='{p_color}'><b>{r.get('priority', 'Medium')}</b></font>", body_style),
                Paragraph(r.get("category", "General"), body_style),
                Paragraph(r.get("text", r.get("recommendation_text", "")), body_style)
            ])
        t_rec = Table(rec_table_data, colWidths=[1.1 * inch, 1.8 * inch, 4.3 * inch])
        t_rec.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F8FAFC")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t_rec)
        story.append(Spacer(1, 10))

    # Faculty Remarks
    if faculty_remarks:
        story.append(Paragraph("Faculty Academic Advisor Remarks", h2_style))
        t_remarks = Table([[Paragraph(f"\"{faculty_remarks}\"", body_style)]], colWidths=[7.2 * inch])
        t_remarks.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FFFBEB")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#FCD34D")),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(t_remarks)
        story.append(Spacer(1, 10))

    # 6. Official Disclaimer (Required by Section 10)
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceBefore=6, spaceAfter=6))
    disclaimer_text = (
        "<b>Important Academic Advisory Notice:</b> Model output is an empirical statistical estimate based on historical "
        "and continuous assessment records; it should be reviewed alongside qualitative context and instructor appraisal. "
        "Predictions support human review and timely guidance—they must not replace faculty judgment, nor serve as the sole "
        "basis for penalties, course progression, or academic standing decisions."
    )
    story.append(Paragraph(disclaimer_text, disclaimer_style))

    doc.build(story)

    if output_path:
        with open(output_path, "rb") as f:
            return f.read()
    else:
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

