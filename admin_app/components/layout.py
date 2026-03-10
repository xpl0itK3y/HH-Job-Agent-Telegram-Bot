from typing import Mapping

import streamlit as st


def apply_app_chrome() -> None:
    st.markdown(
        """
        <style>
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
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(page_registry: Mapping[str, object]) -> str:
    with st.sidebar:
        st.markdown("### HH Job Agent")
        st.caption("Internal admin workspace")
        labels = {key: page.title for key, page in page_registry.items()}
        choice = st.radio(
            "Sections",
            options=list(page_registry.keys()),
            format_func=lambda key: labels[key],
            label_visibility="collapsed",
        )
        st.divider()
        st.caption("Streamlit internal panel")
    return choice
