import streamlit as st

from admin_app.components.tables import dataframe_section
from admin_app.services.db_service import AdminDBService


class UsersPage:
    title = "Users"

    def __init__(self) -> None:
        self.db = AdminDBService()

    def render(self) -> None:
        st.markdown('<div class="admin-page-title">Users</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="admin-page-subtitle">Search and inspect registered Telegram users.</div>',
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("Username contains", placeholder="denis")
        with col2:
            status = st.selectbox("Bot status", options=["all", "active", "paused"])

        filters = {
            "username": username or None,
            "bot_status": None if status == "all" else status,
        }
        rows = self.db.get_users(filters=filters, limit=50)
        dataframe_section("Users", rows)
