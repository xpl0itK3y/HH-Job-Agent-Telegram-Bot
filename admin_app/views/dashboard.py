import streamlit as st

from admin_app.components.cards import metric_card
from admin_app.components.page_header import render_page_header
from admin_app.components.tables import dataframe_section
from admin_app.services.analytics_service import AnalyticsService


class DashboardPage:
    title = "Dashboard"

    def __init__(self) -> None:
        self.analytics = AnalyticsService()

    def render(self) -> None:
        summary = self.analytics.get_dashboard_summary()
        country_split = self.analytics.get_country_split()
        activity = self.analytics.get_vacancy_activity()
        failures = self.analytics.get_recent_failures()

        render_page_header("Dashboard", "Operational view over users, vacancies and queue health.")
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

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        col5, col6, col7, col8 = st.columns(4)
        with col5:
            metric_card("Queued", str(summary["queued_total"]), "Waiting in pipeline")
        with col6:
            metric_card("Processing", str(summary["processing_total"]), "Currently running")
        with col7:
            metric_card("Failed", str(summary["failed_total"]), "Require attention")
        with col8:
            metric_card("Sent Today", str(summary["sent_today"]), "Delivered today")

        st.markdown("<div style='height: 1.1rem;'></div>", unsafe_allow_html=True)

        left, right = st.columns([1.4, 1])
        with left:
            dataframe_section("Recent sent vacancies", self.analytics.get_recent_sent_vacancies())
        with right:
            dataframe_section("Recent users", self.analytics.get_recent_users())

        st.markdown("<div style='height: 0.6rem;'></div>", unsafe_allow_html=True)

        chart_col, split_col = st.columns([1.4, 1])
        with chart_col:
            st.markdown("#### Vacancy activity")
            if activity:
                st.line_chart(activity, x="date", y=["queued", "sent"], use_container_width=True)
            else:
                st.info("No activity yet.")
        with split_col:
            dataframe_section("Country split", country_split)

        st.markdown("<div style='height: 0.6rem;'></div>", unsafe_allow_html=True)

        dataframe_section("Recent failures", failures)
