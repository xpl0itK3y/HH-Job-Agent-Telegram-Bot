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
            '<div class="admin-page-subtitle">Full user workspace with profile, resume, settings, sent vacancies and chat.</div>',
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

        overview_tab, resume_tab, settings_tab, sent_tab, chat_tab, errors_tab = st.tabs(
            ["Overview", "Resume", "Search Settings", "Sent Vacancies", "Chat History", "Errors"]
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
                        "recent_errors": len(detail["recent_errors"]),
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
                meta_left, meta_right, meta_third = st.columns(3)
                with meta_left:
                    st.text_input("File path", value=resume["file_path"] or "", disabled=True)
                with meta_right:
                    st.text_input("LLM model", value=resume["llm_model_name"] or "", disabled=True)
                with meta_third:
                    st.text_input("Prompt version", value=resume["llm_prompt_version"] or "", disabled=True)
                if resume["llm_generated_at"]:
                    st.caption(f"LLM generated at {resume['llm_generated_at']}")
                if resume["summary"]:
                    st.text_area("AI summary", value=resume["summary"], height=120, disabled=True)
                st.text_area("Raw text", value=resume["raw_text"], height=260, disabled=True)
                if resume["parsed_profile_json"]:
                    st.code(json.dumps(resume["parsed_profile_json"], ensure_ascii=False, indent=2), language="json")

        with settings_tab:
            if detail["search_setting"] is None:
                st.info("No search settings saved.")
            else:
                settings = detail["search_setting"]
                top_left, top_right = st.columns(2)
                with top_left:
                    st.text_input("Keywords", value=settings["keywords"] or "", disabled=True)
                    st.text_input(
                        "Countries",
                        value=", ".join(settings["selected_countries_json"] or []),
                        disabled=True,
                    )
                    st.text_input("Areas", value=", ".join(str(v) for v in (settings["area_ids_json"] or [])), disabled=True)
                with top_right:
                    st.text_input("Employment type", value=settings["employment_type"] or "", disabled=True)
                    st.text_input("Work format", value=settings["work_format"] or "", disabled=True)
                    st.text_input("Professional role", value=settings["professional_role"] or "", disabled=True)
                st.text_input("Enabled", value="yes" if settings["is_enabled"] else "no", disabled=True)
                if settings["search_extra_json"]:
                    st.code(json.dumps(settings["search_extra_json"], ensure_ascii=False, indent=2), language="json")

        with sent_tab:
            sent_rows = detail["sent_vacancies"]
            dataframe_section(
                "Sent vacancies",
                [
                    {
                        "id": row["id"],
                        "tag": row["tag"],
                        "title": row["title"],
                        "company_name": row["company_name"],
                        "status": row["status"],
                        "score": row["score"],
                        "sent_at": row["sent_at"],
                    }
                    for row in sent_rows
                ],
            )
            if sent_rows:
                selected_tag = st.selectbox(
                    "Inspect sent vacancy",
                    options=[row["tag"] for row in sent_rows],
                )
                selected = next(row for row in sent_rows if row["tag"] == selected_tag)
                top_left, top_right, top_third = st.columns(3)
                with top_left:
                    st.text_input("Vacancy title", value=selected["title"] or "", disabled=True)
                    st.text_input("Company", value=selected["company_name"] or "", disabled=True)
                    st.text_input("Provider", value=selected["provider"] or "", disabled=True)
                with top_right:
                    st.text_input("Status", value=selected["status"], disabled=True)
                    st.text_input("Score", value=str(selected["score"] or ""), disabled=True)
                    st.text_input("Step", value=selected["step"] or "", disabled=True)
                with top_third:
                    st.text_input("Country", value=selected["source_country_code"] or "", disabled=True)
                    st.text_input("Message id", value=selected["message_id"] or "", disabled=True)
                    st.text_input("Sent at", value=selected["sent_at"] or "", disabled=True)
                if selected["match_summary"]:
                    st.text_area("Match summary", value=selected["match_summary"], height=120, disabled=True)
                if selected["cover_letter"]:
                    st.text_area("Cover letter", value=selected["cover_letter"], height=180, disabled=True)
                if selected["missing_skills_json"]:
                    st.code(json.dumps(selected["missing_skills_json"], ensure_ascii=False, indent=2), language="json")
                if selected["employer_check_json"]:
                    st.code(json.dumps(selected["employer_check_json"], ensure_ascii=False, indent=2), language="json")
                vacancy_tabs = st.tabs(["AI Summary", "Clean Description", "Raw Description"])
                with vacancy_tabs[0]:
                    st.text_area(
                        "description_ai_summary",
                        value=selected["description_ai_summary"] or "",
                        height=180,
                        disabled=True,
                    )
                with vacancy_tabs[1]:
                    st.text_area(
                        "description_clean",
                        value=selected["description_clean"] or "",
                        height=260,
                        disabled=True,
                    )
                with vacancy_tabs[2]:
                    st.text_area(
                        "description_raw",
                        value=selected["description_raw"] or "",
                        height=260,
                        disabled=True,
                    )

        with chat_tab:
            chat_rows = detail["chat_messages"]
            dataframe_section("Chat history", chat_rows)

        with errors_tab:
            dataframe_section("Recent errors", detail["recent_errors"])
