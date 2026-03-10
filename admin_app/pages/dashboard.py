import streamlit as st

from admin_app.components.cards import metric_card
from admin_app.components.tables import dataframe_section
from admin_app.services.analytics_service import AnalyticsService


class DashboardPage:
    title = "Dashboard"

    def __init__(self) -> None:
        self.analytics = AnalyticsService()

    def render(self) -> None:
        summary = self.analytics.get_dashboard_summary()
        st.markdown('<div class="admin-page-title">Dashboard</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="admin-page-subtitle">Operational view over users, vacancies and queue health.</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="admin-hero">
                <strong>Control room</strong><br/>
                Track onboarding flow, vacancy pipeline and delivery issues from one internal panel.
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            metric_card("Users", str(summary["users_total"]), "Registered users")
        with col2:
            metric_card("Active", str(summary["users_active"]), "Bot running")
        with col3:
            metric_card("Paused", str(summary["users_paused"]), "Search paused")
        with col4:
            metric_card("Vacancies", str(summary["vacancies_total"]), "Normalized vacancies")

        col5, col6, col7, col8 = st.columns(4)
        with col5:
            metric_card("Queued", str(summary["queued_total"]), "Waiting in pipeline")
        with col6:
            metric_card("Processing", str(summary["processing_total"]), "Currently running")
        with col7:
            metric_card("Failed", str(summary["failed_total"]), "Require attention")
        with col8:
            metric_card("Sent Today", str(summary["sent_today"]), "Delivered today")

        left, right = st.columns([1.4, 1])
        with left:
            dataframe_section("Recent sent vacancies", self.analytics.get_recent_sent_vacancies())
        with right:
            dataframe_section("Recent users", self.analytics.get_recent_users())
