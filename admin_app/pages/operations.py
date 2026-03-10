import streamlit as st

from admin_app.components.cards import metric_card
from admin_app.components.tables import dataframe_section
from admin_app.services.db_service import AdminDBService


class OperationsPage:
    title = "Operations"

    def __init__(self) -> None:
        self.db = AdminDBService()

    def render(self) -> None:
        st.markdown('<div class="admin-page-title">Operations</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="admin-page-subtitle">Queue monitor, Redis locks and operational error feed in one place.</div>',
            unsafe_allow_html=True,
        )

        queue_snapshot = self.db.get_queue_snapshot(limit=100)
        logs = self.db.get_operational_logs(limit=100)

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            metric_card("Queued", str(queue_snapshot["summary"]["queued"]), "Waiting in queue")
        with col2:
            metric_card("Processing", str(queue_snapshot["summary"]["processing"]), "In progress")
        with col3:
            metric_card("Ready", str(queue_snapshot["summary"]["ready_to_send"]), "Ready to send")
        with col4:
            metric_card("Failed", str(queue_snapshot["summary"]["failed"]), "Need attention")
        with col5:
            metric_card("Stalled", str(queue_snapshot["summary"]["stalled"]), "Processing > 15 min")

        queue_tab, logs_tab = st.tabs(["Queue Monitor", "Logs"])

        with queue_tab:
            left, right = st.columns([1.5, 1])
            with left:
                dataframe_section("Queue items", queue_snapshot["queue_items"])
            with right:
                dataframe_section("Active Redis locks", queue_snapshot["locks"])
            dataframe_section("Scheduled reminders", queue_snapshot["reminders"])

        with logs_tab:
            dataframe_section("Operational logs", logs)
