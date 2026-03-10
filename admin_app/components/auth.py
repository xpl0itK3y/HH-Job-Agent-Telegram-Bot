import streamlit as st

from admin_app.services.auth_service import AdminAuthService


def require_authentication() -> dict:
    auth_state = st.session_state.setdefault("admin_auth", {})
    if auth_state.get("is_authenticated"):
        return auth_state

    service = AdminAuthService()
    left, center, right = st.columns([1, 1.2, 1])
    with center:
        st.markdown('<div class="admin-page-title">Admin Login</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="admin-page-subtitle">Restricted access for internal operators only.</div>',
            unsafe_allow_html=True,
        )
        with st.form("admin-login", clear_on_submit=False):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)
        if submitted:
            result = service.authenticate(username=username.strip(), password=password)
            if result is None:
                st.error("Invalid credentials.")
            else:
                st.session_state["admin_auth"] = {
                    "is_authenticated": True,
                    "admin_user_id": result.admin_user_id,
                    "username": result.username,
                    "role": result.role,
                }
                st.rerun()
    st.stop()
