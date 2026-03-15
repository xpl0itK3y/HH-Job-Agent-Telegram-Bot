import json

import streamlit as st

from admin_app.components.page_header import render_page_header
from admin_app.components.tables import dataframe_section
from admin_app.services.db_service import AdminDBService


class SearchSettingsPage:
    title = "Search Settings"

    def __init__(self) -> None:
        self.db = AdminDBService()

    def render(self) -> None:
        render_page_header(
            "Search Settings",
            "Registry of saved user filters, countries and search state.",
        )

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            user_id_raw = st.text_input("User id", placeholder="42")
        with col2:
            username = st.text_input("Username", placeholder="denis")
        with col3:
            country = st.selectbox("Country", ["all", "KZ", "RU"])
        with col4:
            enabled = st.selectbox("Enabled", ["all", "yes", "no"])

        user_id = int(user_id_raw) if user_id_raw.strip().isdigit() else None
        rows = self.db.get_search_settings(
            filters={
                "user_id": user_id,
                "username": username or None,
                "country": None if country == "all" else country,
                "is_enabled": None if enabled == "all" else enabled == "yes",
            },
            limit=100,
        )

        dataframe_section(
            "Search settings",
            [
                {
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "username": row["username"],
                    "countries": ", ".join(row["selected_countries_json"] or []),
                    "keywords": row["keywords"],
                    "is_enabled": row["is_enabled"],
                    "updated_at": row["updated_at"],
                }
                for row in rows
            ],
        )

        if rows:
            setting_id = st.selectbox("Inspect settings", options=[row["id"] for row in rows])
            setting = next(row for row in rows if row["id"] == setting_id)
            left, right = st.columns(2)
            with left:
                st.text_input("User id", value=str(setting["user_id"]), disabled=True)
                st.text_input("Username", value=setting["username"] or "", disabled=True)
                st.text_input("Keywords", value=setting["keywords"] or "", disabled=True)
                st.text_input(
                    "Countries",
                    value=", ".join(setting["selected_countries_json"] or []),
                    disabled=True,
                )
            with right:
                st.text_input("Employment", value=setting["employment_type"] or "", disabled=True)
                st.text_input("Work format", value=setting["work_format"] or "", disabled=True)
                st.text_input("Professional role", value=setting["professional_role"] or "", disabled=True)
                st.text_input("Enabled", value="yes" if setting["is_enabled"] else "no", disabled=True)
            st.text_input(
                "Area ids",
                value=", ".join(str(area_id) for area_id in (setting["area_ids_json"] or [])),
                disabled=True,
            )
            if setting["search_extra_json"]:
                st.code(json.dumps(setting["search_extra_json"], ensure_ascii=False, indent=2), language="json")
