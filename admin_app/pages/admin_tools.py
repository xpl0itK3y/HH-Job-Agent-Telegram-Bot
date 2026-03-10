import streamlit as st

from admin_app.services.admin_actions_service import AdminActionsService


class AdminToolsPage:
    title = "Admin Tools"

    def __init__(self) -> None:
        self.actions = AdminActionsService()

    def render(self) -> None:
        st.markdown('<div class="admin-page-title">Admin Tools</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="admin-page-subtitle">Manual operator actions for user status and queue recovery.</div>',
            unsafe_allow_html=True,
        )

        admin_user_id = st.session_state.get("admin_auth", {}).get("admin_user_id")
        user_tab, resume_tab, queue_tab = st.tabs(["User Controls", "Resume", "Queue Recovery"])

        with user_tab:
            user_id = st.number_input("User id", min_value=1, step=1, key="admin_tools_user_id")
            left, right = st.columns(2)
            with left:
                if st.button("Pause User", use_container_width=True):
                    self._show_result(self.actions.pause_user(int(user_id), admin_user_id=admin_user_id))
            with right:
                if st.button("Resume User", use_container_width=True):
                    self._show_result(self.actions.resume_user(int(user_id), admin_user_id=admin_user_id))

        with resume_tab:
            resume_user_id = st.number_input("Resume user id", min_value=1, step=1, key="admin_tools_resume_user_id")
            if st.button("Reprocess Resume", use_container_width=True):
                self._show_result(self.actions.reprocess_resume(int(resume_user_id), admin_user_id=admin_user_id))

        with queue_tab:
            sent_vacancy_id = st.number_input("Sent vacancy id", min_value=1, step=1, key="admin_tools_sent_vacancy_id")
            left, center, right = st.columns(3)
            with left:
                if st.button("Move To Queue", use_container_width=True):
                    self._show_result(
                        self.actions.requeue_sent_vacancy(int(sent_vacancy_id), admin_user_id=admin_user_id)
                    )
            with center:
                if st.button("Rerun Vacancy", use_container_width=True):
                    self._show_result(
                        self.actions.rerun_sent_vacancy(int(sent_vacancy_id), admin_user_id=admin_user_id)
                    )
            with right:
                error_text = st.text_input(
                    "Failure reason",
                    value="Manually marked as failed",
                    key="admin_tools_failure_reason",
                )
                if st.button("Mark Failed", use_container_width=True):
                    self._show_result(
                        self.actions.mark_sent_vacancy_failed(
                            int(sent_vacancy_id),
                            error_text,
                            admin_user_id=admin_user_id,
                        )
                    )

    @staticmethod
    def _show_result(result: dict) -> None:
        if result["ok"]:
            st.success(result["message"])
        else:
            st.error(result["message"])
