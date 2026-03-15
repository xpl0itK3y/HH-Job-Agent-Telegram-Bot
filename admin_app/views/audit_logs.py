import json

import streamlit as st

from admin_app.components.page_header import render_page_header
from admin_app.components.tables import dataframe_section
from admin_app.services.db_service import AdminDBService


class AuditLogsPage:
    title = "Audit Logs"

    def __init__(self) -> None:
        self.db = AdminDBService()

    def render(self) -> None:
        render_page_header(
            "Audit Logs",
            "Destructive and operator actions recorded in admin_audit_logs.",
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            admin_username = st.text_input("Admin username", placeholder="admin")
        with col2:
            action_type = st.text_input("Action type", placeholder="delete_user")
        with col3:
            entity_type = st.selectbox("Entity type", ["all", "user", "resume", "vacancy", "sent_vacancy"])

        rows = self.db.get_admin_audit_logs(
            filters={
                "admin_username": admin_username or None,
                "action_type": action_type or None,
                "entity_type": None if entity_type == "all" else entity_type,
            },
            limit=200,
        )
        dataframe_section(
            "Audit log",
            [
                {
                    "id": row["id"],
                    "admin_username": row["admin_username"],
                    "action_type": row["action_type"],
                    "entity_type": row["entity_type"],
                    "entity_id": row["entity_id"],
                    "created_at": row["created_at"],
                }
                for row in rows
            ],
        )

        if rows:
            audit_id = st.selectbox("Inspect audit entry", options=[row["id"] for row in rows])
            audit = next(row for row in rows if row["id"] == audit_id)
            left, right = st.columns(2)
            with left:
                st.text_input("Admin", value=audit["admin_username"], disabled=True)
                st.text_input("Action", value=audit["action_type"], disabled=True)
                st.text_input("Entity type", value=audit["entity_type"], disabled=True)
            with right:
                st.text_input("Entity id", value=audit["entity_id"], disabled=True)
                st.text_input("Created at", value=audit["created_at"], disabled=True)
                st.text_input("Admin user id", value=str(audit["admin_user_id"]), disabled=True)
            if audit["details_json"]:
                st.code(json.dumps(audit["details_json"], ensure_ascii=False, indent=2), language="json")
