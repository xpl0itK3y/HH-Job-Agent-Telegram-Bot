import streamlit as st


def metric_card(label: str, value: str, caption: str) -> None:
    st.markdown(
        f"""
        <div class="admin-card">
            <div class="admin-metric-label">{label}</div>
            <div class="admin-metric-value">{value}</div>
            <div style="color:#94a3b8">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
