import json

import streamlit as st

from admin_app.components.tables import dataframe_section
from admin_app.services.db_service import AdminDBService


class UserDetailPage:
    title = "User Detail"

    def __init__(self) -> None:
        self.db = AdminDBService()

    def render(self) -> None:
        st.markdown('<div class="admin-page-title">User Detail</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="admin-page-subtitle">Full user profile with resume, settings and recent activity.</div>',
            unsafe_allow_html=True,
        )

        top_left, top_right = st.columns([1, 4])
        with top_left:
            if st.button("Back to Users", use_container_width=True):
                st.session_state["admin_page"] = "users"
                st.rerun()

        selected_user_id = st.session_state.get("admin_selected_user_id")
        user_id = st.number_input(
            "User id",
            min_value=1,
            step=1,
            value=int(selected_user_id or 1),
        )
        st.session_state["admin_selected_user_id"] = int(user_id)

        detail = self.db.get_user_detail(int(user_id))
        if detail is None:
            st.warning("User not found.")
            return

        user = detail["user"]
        display_name = user["username"] or f"telegram:{user['telegram_user_id']}"
        st.markdown(f"### {display_name}")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Telegram ID", str(user["telegram_user_id"]))
        with col2:
            st.metric("Status", user["bot_status"])
        with col3:
            st.metric("Language", user["language_code"] or "n/a")
        with col4:
            st.metric("Active", "yes" if user["is_active"] else "no")

        overview_tab, resume_tab, settings_tab, activity_tab = st.tabs(
            ["Overview", "Resume", "Search Settings", "Activity"]
        )

        with overview_tab:
            left, right = st.columns([1, 1.2])
            with left:
                st.markdown("#### Profile")
                st.json(user, expanded=False)
            with right:
                st.markdown("#### Snapshot")
                st.json(
                    {
                        "has_resume": detail["resume"] is not None,
                        "has_search_setting": detail["search_setting"] is not None,
                        "sent_vacancies": len(detail["sent_vacancies"]),
                        "chat_messages": len(detail["chat_messages"]),
                    },
                    expanded=False,
                )

        with resume_tab:
            if detail["resume"] is None:
                st.info("No resume uploaded.")
            else:
                resume = detail["resume"]
                st.caption(f"Updated at {resume['updated_at']}")
                meta_left, meta_right = st.columns(2)
                with meta_left:
                    st.text_input("Source type", value=resume["source_type"], disabled=True)
                with meta_right:
                    st.text_input("Resume link", value=resume["resume_link"] or "", disabled=True)
                if resume["summary"]:
                    st.text_area("AI summary", value=resume["summary"], height=120, disabled=True)
                st.text_area("Raw text", value=resume["raw_text"], height=260, disabled=True)
                if resume["parsed_profile_json"]:
                    st.code(json.dumps(resume["parsed_profile_json"], ensure_ascii=False, indent=2), language="json")

        with settings_tab:
            if detail["search_setting"] is None:
                st.info("No search settings saved.")
            else:
                st.json(detail["search_setting"], expanded=False)

        with activity_tab:
            left, right = st.columns(2)
            with left:
                dataframe_section("Recent sent vacancies", detail["sent_vacancies"])
            with right:
                dataframe_section("Recent chat messages", detail["chat_messages"])
