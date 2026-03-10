import streamlit as st

from admin_app.components.tables import dataframe_section
from admin_app.services.db_service import AdminDBService


class ChatHistoryPage:
    title = "Chat History"

    def __init__(self) -> None:
        self.db = AdminDBService()

    def render(self) -> None:
        st.markdown('<div class="admin-page-title">Chat History</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="admin-page-subtitle">Global Q&A history across users and vacancy tags.</div>',
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            user_id_raw = st.text_input("User id", placeholder="42")
        with col2:
            vacancy_tag = st.text_input("Vacancy tag", placeholder="#VAC_12345")
        with col3:
            role = st.selectbox("Role", ["all", "user", "assistant", "system"])

        user_id = int(user_id_raw) if user_id_raw.strip().isdigit() else None
        rows = self.db.get_chat_history(
            filters={
                "user_id": user_id,
                "vacancy_tag": vacancy_tag or None,
                "role": None if role == "all" else role,
            },
            limit=200,
        )

        dataframe_section(
            "Chat messages",
            [
                {
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "vacancy_tag": row["vacancy_tag"],
                    "role": row["role"],
                    "created_at": row["created_at"],
                }
                for row in rows
            ],
        )

        if rows:
            message_id = st.selectbox("Inspect message", options=[row["id"] for row in rows])
            message = next(row for row in rows if row["id"] == message_id)
            left, right = st.columns(2)
            with left:
                st.text_input("User id", value=str(message["user_id"]), disabled=True)
                st.text_input("Username", value=message["username"] or "", disabled=True)
                st.text_input("Telegram id", value=str(message["telegram_user_id"]), disabled=True)
                st.text_input("Role", value=message["role"], disabled=True)
            with right:
                st.text_input("Vacancy id", value=str(message["vacancy_id"]), disabled=True)
                st.text_input("Vacancy tag", value=message["vacancy_tag"] or "", disabled=True)
                st.text_input("Vacancy title", value=message["vacancy_title"] or "", disabled=True)
                st.text_input("Created at", value=message["created_at"], disabled=True)
            st.text_area("Message", value=message["message_text"], height=220, disabled=True)
