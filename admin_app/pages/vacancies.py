import json

import streamlit as st

from admin_app.components.tables import dataframe_section
from admin_app.services.db_service import AdminDBService


class VacanciesPage:
    title = "Vacancies"

    def __init__(self) -> None:
        self.db = AdminDBService()

    def render(self) -> None:
        st.markdown('<div class="admin-page-title">Vacancies</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="admin-page-subtitle">Compact workspace for vacancy catalog and sent history.</div>',
            unsafe_allow_html=True,
        )

        catalog_tab, sent_tab = st.tabs(["Catalog", "Sent Vacancies"])

        with catalog_tab:
            self._render_catalog()

        with sent_tab:
            self._render_sent_vacancies()

    def _render_catalog(self) -> None:
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            provider = st.selectbox("Provider", ["all", "hh_kz", "hh_ru"])
        with col2:
            country = st.selectbox("Country", ["all", "KZ", "RU"])
        with col3:
            company_name = st.text_input("Company", placeholder="Kaspi")
        with col4:
            title = st.text_input("Title", placeholder="Python")
        with col5:
            summary_filter = st.selectbox("AI summary", ["all", "yes", "no"])

        rows = self.db.get_vacancies(
            filters={
                "provider": None if provider == "all" else provider,
                "country": None if country == "all" else country,
                "company_name": company_name or None,
                "title": title or None,
                "has_ai_summary": None if summary_filter == "all" else summary_filter == "yes",
            },
            limit=100,
        )
        dataframe_section(
            "Vacancy catalog",
            [
                {
                    "id": row["id"],
                    "provider": row["provider"],
                    "country": row["source_country_code"],
                    "title": row["title"],
                    "company_name": row["company_name"],
                    "salary": row["salary"],
                    "has_ai_summary": row["has_ai_summary"],
                    "fetched_at": row["fetched_at"],
                }
                for row in rows
            ],
        )
        if rows:
            vacancy_id = st.selectbox("Inspect vacancy", options=[row["id"] for row in rows])
            vacancy = next(row for row in rows if row["id"] == vacancy_id)
            top_left, top_right = st.columns(2)
            with top_left:
                st.text_input("Title", value=vacancy["title"], disabled=True)
                st.text_input("Company", value=vacancy["company_name"], disabled=True)
                st.text_input("Provider", value=vacancy["provider"], disabled=True)
                st.text_input("Country", value=vacancy["source_country_code"], disabled=True)
            with top_right:
                st.text_input("Salary", value=vacancy["salary"], disabled=True)
                st.text_input("Employment", value=vacancy["employment_type"] or "", disabled=True)
                st.text_input("Format", value=vacancy["work_format"] or "", disabled=True)
                st.text_input("Area", value=vacancy["area_name"] or "", disabled=True)
            st.text_input("URL", value=vacancy["alternate_url"] or "", disabled=True)
            if vacancy["key_skills_json"]:
                st.code(json.dumps(vacancy["key_skills_json"], ensure_ascii=False, indent=2), language="json")
            detail_tabs = st.tabs(["AI Summary", "Clean Description", "Raw Description"])
            with detail_tabs[0]:
                st.text_area("description_ai_summary", value=vacancy["description_ai_summary"] or "", height=180, disabled=True)
            with detail_tabs[1]:
                st.text_area("description_clean", value=vacancy["description_clean"] or "", height=260, disabled=True)
            with detail_tabs[2]:
                st.text_area("description_raw", value=vacancy["description_raw"] or "", height=260, disabled=True)

    def _render_sent_vacancies(self) -> None:
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            user_id_raw = st.text_input("User id", placeholder="42")
        with col2:
            status = st.selectbox("Status", ["all", "queued", "processing", "ready_to_send", "sent", "failed"])
        with col3:
            vacancy_tag = st.text_input("Vacancy tag", placeholder="#VAC_12345")
        with col4:
            provider = st.selectbox("Sent provider", ["all", "hh_kz", "hh_ru"])
        with col5:
            cover_letter = st.selectbox("Cover letter", ["all", "yes", "no"])

        user_id = int(user_id_raw) if user_id_raw.strip().isdigit() else None
        rows = self.db.get_sent_vacancies(
            filters={
                "user_id": user_id,
                "status": None if status == "all" else status,
                "vacancy_tag": vacancy_tag or None,
                "provider": None if provider == "all" else provider,
                "has_cover_letter": None if cover_letter == "all" else cover_letter == "yes",
            },
            limit=100,
        )
        dataframe_section(
            "Sent vacancies",
            [
                {
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "vacancy_tag": row["vacancy_tag"],
                    "provider": row["provider"],
                    "title": row["title"],
                    "status": row["processing_status"],
                    "match_score": row["match_score"],
                    "sent_at": row["sent_at"],
                }
                for row in rows
            ],
        )
        if rows:
            sent_id = st.selectbox("Inspect sent vacancy", options=[row["id"] for row in rows])
            sent = next(row for row in rows if row["id"] == sent_id)
            top_left, top_right, top_third = st.columns(3)
            with top_left:
                st.text_input("Tag", value=sent["vacancy_tag"], disabled=True)
                st.text_input("Title", value=sent["title"], disabled=True)
                st.text_input("Company", value=sent["company_name"], disabled=True)
            with top_right:
                st.text_input("User", value=str(sent["user_id"]), disabled=True)
                st.text_input("Status", value=sent["processing_status"], disabled=True)
                st.text_input("Step", value=sent["current_pipeline_step"] or "", disabled=True)
            with top_third:
                st.text_input("Provider", value=sent["provider"], disabled=True)
                st.text_input("Message id", value=sent["telegram_message_id"] or "", disabled=True)
                st.text_input("Sent at", value=sent["sent_at"] or "", disabled=True)
            if sent["match_summary"]:
                st.text_area("Match summary", value=sent["match_summary"], height=120, disabled=True)
            if sent["cover_letter"]:
                st.text_area("Cover letter", value=sent["cover_letter"], height=180, disabled=True)
            detail_left, detail_right = st.columns(2)
            with detail_left:
                if sent["missing_skills_json"]:
                    st.code(json.dumps(sent["missing_skills_json"], ensure_ascii=False, indent=2), language="json")
            with detail_right:
                if sent["employer_check_json"]:
                    st.code(json.dumps(sent["employer_check_json"], ensure_ascii=False, indent=2), language="json")
            st.text_area("description_ai_summary", value=sent["description_ai_summary"] or "", height=160, disabled=True)
            st.text_area("description_clean", value=sent["description_clean"] or "", height=200, disabled=True)
            st.text_input("Vacancy URL", value=sent["alternate_url"] or "", disabled=True)
            if sent["last_error_text"]:
                st.error(sent["last_error_text"])
