import json

import streamlit as st

from admin_app.components.tables import dataframe_section
from admin_app.services.db_service import AdminDBService


class ResumesPage:
    title = "Resumes"

    def __init__(self) -> None:
        self.db = AdminDBService()

    def render(self) -> None:
        st.markdown('<div class="admin-page-title">Resumes</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="admin-page-subtitle">Resume registry with extracted profile and LLM metadata.</div>',
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            user_id_raw = st.text_input("User id", placeholder="42")
        with col2:
            username = st.text_input("Username", placeholder="denis")
        with col3:
            source_type = st.selectbox("Source type", ["all", "pdf", "text", "link"])

        user_id = int(user_id_raw) if user_id_raw.strip().isdigit() else None
        rows = self.db.get_resumes(
            filters={
                "user_id": user_id,
                "username": username or None,
                "source_type": None if source_type == "all" else source_type,
            },
            limit=100,
        )

        dataframe_section(
            "Resumes",
            [
                {
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "username": row["username"],
                    "source_type": row["source_type"],
                    "llm_model_name": row["llm_model_name"],
                    "updated_at": row["updated_at"],
                }
                for row in rows
            ],
        )

        if rows:
            resume_id = st.selectbox("Inspect resume", options=[row["id"] for row in rows])
            resume = next(row for row in rows if row["id"] == resume_id)
            top_left, top_right = st.columns(2)
            with top_left:
                st.text_input("User", value=str(resume["user_id"]), disabled=True)
                st.text_input("Username", value=resume["username"] or "", disabled=True)
                st.text_input("Source type", value=resume["source_type"], disabled=True)
                st.text_input("Resume link", value=resume["resume_link"] or "", disabled=True)
            with top_right:
                st.text_input("File path", value=resume["file_path"] or "", disabled=True)
                st.text_input("LLM model", value=resume["llm_model_name"] or "", disabled=True)
                st.text_input("Prompt version", value=resume["llm_prompt_version"] or "", disabled=True)
                st.text_input("Generated at", value=resume["llm_generated_at"] or "", disabled=True)
            if resume["summary"]:
                st.text_area("AI summary", value=resume["summary"], height=120, disabled=True)
            st.text_area("Raw text", value=resume["raw_text"], height=280, disabled=True)
            if resume["parsed_profile_json"]:
                st.code(json.dumps(resume["parsed_profile_json"], ensure_ascii=False, indent=2), language="json")
