import streamlit as st

from admin_app.components.auth import clear_auth_state, require_authentication
from admin_app.components.layout import apply_app_chrome, render_sidebar
from admin_app.pages import PAGE_REGISTRY


st.set_page_config(
    page_title="HH Job Agent Admin",
    page_icon="HH",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_app_chrome()
auth_state = require_authentication()

page_key = render_sidebar(PAGE_REGISTRY)
page = PAGE_REGISTRY[page_key]

with st.sidebar:
    st.caption(f"Signed in as {auth_state['username']} ({auth_state['role']})")
    if st.button("Log Out", use_container_width=True):
        clear_auth_state()
        st.rerun()

page.render()
