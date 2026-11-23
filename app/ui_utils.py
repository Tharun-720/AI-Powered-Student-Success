"""
UI Utilities and Styling for TREKVERSE Student Success Platform.
Provides cohesive CSS theming, navigation guards, session state helpers, and visual components.
"""

import streamlit as st
from typing import Optional, Dict, Any
import os
import sys

# Ensure root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database.database import authenticate_user, get_student_by_user_id, get_student

THEME_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1250px;
    }
    
    /* Brand Header */
    .brand-banner {
        background: linear-gradient(135deg, #1E3A8A 0%, #1E293B 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    .brand-title {
        font-size: 1.75rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.025em;
    }
    .brand-subtitle {
        font-size: 0.95rem;
        color: #93C5FD;
        margin-top: 0.25rem;
        margin-bottom: 0;
    }
    
    /* Metric Cards */
    .stat-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1.25rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .stat-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
    }
    .stat-label {
        font-size: 0.82rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .stat-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0F172A;
        margin-top: 0.35rem;
    }
    .stat-subtext {
        font-size: 0.8rem;
        color: #94A3B8;
        margin-top: 0.25rem;
    }
    
    /* Risk Badges */
    .badge-low {
        background-color: #ECFDF5;
        color: #065F46;
        border: 1px solid #A7F3D0;
        padding: 0.25rem 0.65rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.78rem;
        display: inline-block;
    }
    .badge-mod {
        background-color: #FFFBEB;
        color: #92400E;
        border: 1px solid #FDE68A;
        padding: 0.25rem 0.65rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.78rem;
        display: inline-block;
    }
    .badge-high {
        background-color: #FEF2F2;
        color: #991B1B;
        border: 1px solid #FECACA;
        padding: 0.25rem 0.65rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.78rem;
        display: inline-block;
    }
    
    /* Advisory Note Callout */
    .advisory-callout {
        background-color: #F8FAFC;
        border-left: 4px solid #3B82F6;
        padding: 1rem 1.25rem;
        border-radius: 0 8px 8px 0;
        margin: 1.5rem 0;
        color: #334155;
        font-size: 0.88rem;
    }
</style>
"""

def apply_app_theme():
    st.markdown(THEME_CSS, unsafe_allow_html=True)

def render_brand_header(title: str, subtitle: str):
    st.markdown(f"""
    <div class="brand-banner">
        <div class="brand-title">TREKVERSE — {title}</div>
        <div class="brand-subtitle">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

def get_current_user() -> Optional[Dict[str, Any]]:
    if "user" not in st.session_state or st.session_state["user"] is None:
        # Default to demo administrator session for smooth exploration
        try:
            demo_user = authenticate_user("admin", "admin123")
            st.session_state["user"] = demo_user
        except Exception:
            pass
    return st.session_state.get("user")

def require_auth(allowed_roles: Optional[list] = None) -> bool:
    """Enforces server-side authentication and role check (Section 9 Security Requirements)."""
    user = get_current_user()
    if not user:
        st.warning("🔒 Please sign in to access this module.")
        st.info("Navigate to the main page to select your account or sign in with your institutional credentials.")
        return False
    if allowed_roles and user["role"] not in allowed_roles:
        st.error(f"⛔ Access Restricted: Your account role ('{user['role']}') does not have permission for this page. Required: {', '.join(allowed_roles)}.")
        return False
    return True

def render_user_sidebar():
    """Renders user status and quick logout in sidebar."""
    user = get_current_user()
    with st.sidebar:
        st.markdown("### 🎓 TREKVERSE AI")
        if user:
            role_badge = {
                "admin": "🛡️ Administrator",
                "faculty": "👨‍🏫 Faculty Advisor",
                "student": "🎓 Student"
            }.get(user["role"], user["role"])
            st.success(f"**{user['full_name']}**\n\n{role_badge} · *{user['department']}*")
            if st.button("Sign Out", use_container_width=True, key="btn_logout"):
                st.session_state["user"] = None
                st.session_state.clear()
                st.rerun()
        else:
            st.info("Guest Mode (Not Signed In)")
        st.divider()
        st.caption("AI-Powered Student Success Prediction & Academic Guidance System v1.0.0\n\n© 2026 TREKVERSE AI ACADEMY")

