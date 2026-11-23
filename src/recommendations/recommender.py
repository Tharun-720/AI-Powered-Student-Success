"""
Recommendation and AI Learning Planner module for TREKVERSE Student Success Platform.
Generates personalized weekly study plans, targeted practice topics, and intervention recommendations.
"""

from typing import Dict, List, Any, Optional

SUBJECT_ACTIVITIES = {
    "Mathematics": [
        "Calculus & Linear Algebra core concepts review",
        "Problem set: Differential equations and matrix diagonalization",
        "Previous years' semester exam questions practice",
        "Timed formula recall and speed drill"
    ],
    "Programming": [
        "Data structures implementation (Trees, Heaps, Graphs)",
        "Algorithm debugging and edge case testing",
        "Hands-on coding sprint on competitive platform",
        "Code refactoring and time complexity analysis"
    ],
    "DBMS": [
        "Relational model and normalization (1NF to BCNF) review",
        "Complex SQL queries: Joins, Subqueries, Indexing practice",
        "ACID properties & transaction concurrency control revision",
        "DBMS mock test & ER diagram design exercise"
    ],
    "Computer Networks": [
        "OSI & TCP/IP stack layer protocols deep dive",
        "Subnetting exercises and IP routing algorithms",
        "Packet capture analysis (Wireshark walkthrough)",
        "Network security principles revision"
    ],
    "Electronics": [
        "Semiconductor physics & diode circuit analysis",
        "Op-Amp configurations and active filter calculations",
        "Digital logic gates and Karnaugh mapping exercises",
        "Electronics lab manual revision and circuit simulation"
    ]
}

def generate_personalized_recommendations(
    student_data: Dict[str, Any],
    subject_predictions: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Generates tailored academic guidance based on current metrics, risk band, and subject bottlenecks.
    """
    recs = []
    att = float(student_data.get("attendance", 85.0))
    cgpa = float(student_data.get("previous_cgpa", 7.5))
    backlogs = int(student_data.get("backlogs", 0))
    study_hours = float(student_data.get("study_hours", 2.0))
    
    # 1. Attendance intervention
    if att < 75.0:
        deficit = 75.0 - att
        recs.append({
            "category": "Attendance Improvement",
            "priority": "High",
            "subject": "General Academic Status",
            "text": f"Attendance is currently at {att:.1f}% (below the mandatory 75% threshold). A minimum 2-week consecutive attendance sprint is required to avert exam hall-ticket detention."
        })
    elif att < 80.0:
        recs.append({
            "category": "Attendance Improvement",
            "priority": "Medium",
            "subject": "General Academic Status",
            "text": f"Attendance is borderline ({att:.1f}%). Maintain consistent daily attendance to establish an academic safety margin above 80%."
        })

    # 2. Backlogs resolution
    if backlogs > 0:
        recs.append({
            "category": "Faculty Meeting",
            "priority": "High",
            "subject": "Remedial Backlog Support",
            "text": f"Schedule an academic advising meeting regarding {backlogs} unresolved backlog(s). Register for supplementary tutoring and clear prerequisite hurdles."
        })

    # 3. Study Hours Calibration
    if study_hours < 2.5:
        recs.append({
            "category": "Study Habit",
            "priority": "Medium",
            "subject": "Self-Study Routine",
            "text": f"Current self-study time ({study_hours:.1f} hrs/day) is below recommended semester workload. Target an incremental increase to 3.0-3.5 hrs/day utilizing 45-minute focused blocks."
        })

    # 4. Subject-specific practice areas
    if subject_predictions:
        weak_subjects = [s for s in subject_predictions if s.get("interpretation") == "May need targeted practice"]
        for s in weak_subjects:
            subj = s["subject"]
            recs.append({
                "category": "Topic Revision",
                "priority": "High" if s["predicted_score"] < 13.0 else "Medium",
                "subject": subj,
                "text": f"Forecasted score in {subj} ({s['predicted_score']}/20) signals conceptual difficulty. Dedicate at least 3 hours weekly to foundational problem sets and peer study sessions."
            })

    # Fallback enrichment recommendation
    if not recs:
        recs.append({
            "category": "Study Habit",
            "priority": "Low",
            "subject": "Advanced Honors",
            "text": "Academic indicators are strong across all monitored subjects. Explore advanced capstone projects, research publications, or student mentorship roles."
        })

    return recs

def build_weekly_study_schedule(
    student_data: Dict[str, Any],
    weak_subjects: Optional[List[str]] = None,
    daily_available_hours: float = 2.5
) -> List[Dict[str, Any]]:
    """
    Builds a weekly schedule (Monday - Friday) tailored to student's weak subjects and available study hours.
    Conforms directly to Section 11 Illustrative Activity table.
    """
    if not weak_subjects:
        weak_subjects = ["DBMS", "Mathematics", "Electronics"]

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    primary_weak = weak_subjects[0] if weak_subjects else "DBMS"
    secondary_weak = weak_subjects[1] if len(weak_subjects) > 1 else "Mathematics"

    plan = [
        {
            "day_of_week": "Monday",
            "time_slot": "5:30 PM - 7:00 PM",
            "subject": primary_weak,
            "activity": f"{primary_weak} core concepts & foundational theory review",
            "duration_hours": round(min(1.5, daily_available_hours), 1)
        },
        {
            "day_of_week": "Tuesday",
            "time_slot": "6:00 PM - 7:00 PM",
            "subject": primary_weak,
            "activity": f"{primary_weak} hands-on practice & applied problem set",
            "duration_hours": round(min(1.0, daily_available_hours), 1)
        },
        {
            "day_of_week": "Wednesday",
            "time_slot": "5:30 PM - 6:30 PM",
            "subject": secondary_weak,
            "activity": f"{secondary_weak} review of difficult formulas and theorems",
            "duration_hours": round(min(1.0, daily_available_hours), 1)
        },
        {
            "day_of_week": "Thursday",
            "time_slot": "5:00 PM - 6:30 PM",
            "subject": primary_weak,
            "activity": f"Previous semester exam question papers & revision",
            "duration_hours": round(min(1.5, daily_available_hours), 1)
        },
        {
            "day_of_week": "Friday",
            "time_slot": "6:00 PM - 6:45 PM",
            "subject": "Comprehensive",
            "activity": "Weekly mock assessment & knowledge self-evaluation drill",
            "duration_hours": round(min(0.75, daily_available_hours), 2)
        }
    ]

    return plan

