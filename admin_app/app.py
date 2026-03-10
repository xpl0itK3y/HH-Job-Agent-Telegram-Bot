import streamlit as st

from admin_app.components.layout import apply_app_chrome, render_sidebar
from admin_app.pages import PAGE_REGISTRY


st.set_page_config(
    page_title="HH Job Agent Admin",
    page_icon="HH",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_app_chrome()

page_key = render_sidebar(PAGE_REGISTRY)
page = PAGE_REGISTRY[page_key]

page.render()
