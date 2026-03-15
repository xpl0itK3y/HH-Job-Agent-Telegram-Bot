import streamlit as st

from admin_app.components.page_header import render_page_header
from admin_app.components.tables import dataframe_section
from admin_app.services.db_service import AdminDBService


class UsersPage:
    title = "Users"

    def __init__(self) -> None:
        self.db = AdminDBService()

    def render(self) -> None:
        render_page_header("Users", "Search and inspect registered Telegram users.")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            telegram_user_id_raw = st.text_input("Telegram user id", placeholder="123456789")
        with col2:
            username = st.text_input("Username contains", placeholder="denis")
        with col3:
            status = st.selectbox("Bot status", options=["all", "active", "paused"])
        with col4:
            country = st.selectbox("Country", options=["all", "KZ", "RU"])

        telegram_user_id = None
        if telegram_user_id_raw.strip():
            if telegram_user_id_raw.strip().isdigit():
                telegram_user_id = int(telegram_user_id_raw.strip())
            else:
                st.warning("Telegram user id must contain digits only.")

        filters = {
            "telegram_user_id": telegram_user_id,
            "username": username or None,
            "bot_status": None if status == "all" else status,
            "country": None if country == "all" else country,
        }
        rows = self.db.get_users(filters=filters, limit=50)
        st.caption(f"Found {len(rows)} users")
        dataframe_section("Users", rows)

        if rows:
            selected_user_id = st.selectbox(
                "Open user profile",
                options=[row["id"] for row in rows],
                format_func=lambda user_id: next(
                    (
                        f"#{row['id']} @{row['username']}"
                        if row["username"]
                        else f"#{row['id']} telegram:{row['telegram_user_id']}"
                    )
                    for row in rows
                    if row["id"] == user_id
                ),
            )
            if st.button("Open User Detail", use_container_width=True):
                st.session_state["admin_selected_user_id"] = selected_user_id
                st.session_state["admin_page"] = "user_detail"
                st.rerun()
