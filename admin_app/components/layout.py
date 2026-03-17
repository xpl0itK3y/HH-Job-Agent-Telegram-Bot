from typing import Mapping

import streamlit as st

from admin_app.components.auth import is_admin


def apply_app_chrome() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
        [data-testid="stSidebarContent"] {
            padding-top: 0.5rem;
        }
        [data-testid="stSidebarUserContent"] {
            padding-top: 0.5rem;
        }
        .block-container {
            padding-top: 1.4rem !important;
            padding-left: 1.4rem;
            padding-right: 1.4rem;
            max-width: none;
        }
        [data-testid="stAppViewContainer"] > .main {
            padding-top: 1rem !important;
        }
        [data-testid="stAppViewContainer"] > .main > div:first-child {
            padding-top: 0.75rem !important;
        }
        [data-testid="stAppViewContainer"] .main .block-container {
            padding-top: 1.6rem !important;
            padding-bottom: 2rem;
            padding-left: 1.4rem;
            padding-right: 1.4rem;
            max-width: none;
        }
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(29, 78, 216, 0.18), transparent 28%),
                radial-gradient(circle at top right, rgba(16, 185, 129, 0.14), transparent 24%),
                linear-gradient(180deg, #0b1220 0%, #111827 100%);
            color: #e5eefc;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #08101d 0%, #0f1a2d 100%);
            border-right: 1px solid rgba(148, 163, 184, 0.15);
        }
        section[data-testid="stSidebar"] > div {
            padding-top: 0.35rem;
        }
        .admin-hero {
            padding: 1.2rem 1.4rem;
            border: 1px solid rgba(96, 165, 250, 0.18);
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.92), rgba(30, 41, 59, 0.82));
            border-radius: 20px;
            margin-bottom: 1rem;
            box-shadow: 0 24px 80px rgba(8, 15, 31, 0.35);
        }
        .admin-card {
            border: 1px solid rgba(148, 163, 184, 0.14);
            background: rgba(15, 23, 42, 0.82);
            border-radius: 18px;
            padding: 1rem 1.1rem;
            min-height: 120px;
        }
        .admin-metric-label {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #94a3b8;
        }
        .admin-metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: #f8fafc;
        }
        .admin-page-title {
            font-size: 2.2rem;
            font-weight: 700;
            color: #f8fafc;
            margin-bottom: 0.3rem;
        }
        .admin-page-subtitle {
            color: #94a3b8;
            margin-bottom: 1.4rem;
        }
        .admin-auth-shell {
            padding: 1.25rem 0 0.5rem;
        }
        .admin-auth-card {
            border: 1px solid rgba(148, 163, 184, 0.16);
            background: rgba(15, 23, 42, 0.72);
            border-radius: 18px;
            padding: 0.9rem 1rem 1rem;
            box-shadow: 0 22px 60px rgba(8, 15, 31, 0.28);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(page_registry: Mapping[str, object]) -> str:
    with st.sidebar:
        st.markdown("### HH Job Agent")
        st.caption("Internal admin workspace")
        visible_registry = {
            key: page
            for key, page in page_registry.items()
            if is_admin() or getattr(page, "admin_only", False) is False
        }
        labels = {key: page.title for key, page in visible_registry.items()}
        current_page = st.session_state.get("admin_page", list(visible_registry.keys())[0])
        if current_page not in visible_registry:
            current_page = list(visible_registry.keys())[0]
        if st.session_state.get("admin_sidebar_selection") not in visible_registry:
            st.session_state["admin_sidebar_selection"] = current_page
        choice = st.radio(
            "Sections",
            options=list(visible_registry.keys()),
            format_func=lambda key: labels[key],
            key="admin_sidebar_selection",
            label_visibility="collapsed",
        )
        st.session_state["admin_page"] = choice
        st.divider()
        st.caption("Admin navigation")
    return choice
