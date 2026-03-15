import streamlit as st


def render_page_header(title: str, subtitle: str) -> None:
    st.markdown("<div style='height: 2.25rem;'></div>", unsafe_allow_html=True)
    st.markdown(f'<div class="admin-page-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="admin-page-subtitle">{subtitle}</div>', unsafe_allow_html=True)
