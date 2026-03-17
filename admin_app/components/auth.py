import base64
import hashlib
import hmac
import json
import time

import streamlit as st
import streamlit.components.v1 as components

from admin_app.services.auth_service import AdminAuthService
from app.core.config import get_settings


ADMIN_SESSION_COOKIE = "hh_admin_session"
ADMIN_SESSION_TTL_SECONDS = 60 * 60 * 24 * 7


def get_auth_state() -> dict:
    return st.session_state.setdefault("admin_auth", {})


def is_admin() -> bool:
    return get_auth_state().get("role") == "admin"


def clear_auth_state() -> None:
    st.session_state["admin_auth"] = {}
    _clear_session_cookie()


def require_authentication() -> dict:
    auth_state = get_auth_state()
    _restore_auth_from_cookie()
    auth_state = get_auth_state()
    if auth_state.get("is_authenticated"):
        return auth_state

    service = AdminAuthService()
    st.markdown("<div style='height: 4rem;'></div>", unsafe_allow_html=True)
    left, center, right = st.columns([1, 1.15, 1])
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
                auth_payload = {
                    "is_authenticated": True,
                    "admin_user_id": result.admin_user_id,
                    "username": result.username,
                    "role": result.role,
                }
                st.session_state["admin_auth"] = auth_payload
                _persist_auth_cookie(auth_payload)
                st.rerun()
    st.stop()


def _restore_auth_from_cookie() -> None:
    auth_state = get_auth_state()
    if auth_state.get("is_authenticated"):
        return

    context = getattr(st, "context", None)
    cookies = getattr(context, "cookies", None)
    if cookies is None:
        return

    raw_token = cookies.get(ADMIN_SESSION_COOKIE)
    if not raw_token:
        return

    payload = _decode_signed_payload(raw_token)
    if payload is None:
        _clear_session_cookie()
        return

    st.session_state["admin_auth"] = {
        "is_authenticated": True,
        "admin_user_id": payload.get("admin_user_id"),
        "username": payload["username"],
        "role": payload["role"],
    }


def _persist_auth_cookie(auth_payload: dict) -> None:
    token = _encode_signed_payload(
        {
            "admin_user_id": auth_payload.get("admin_user_id"),
            "username": auth_payload["username"],
            "role": auth_payload["role"],
            "exp": int(time.time()) + ADMIN_SESSION_TTL_SECONDS,
        }
    )
    if token is None:
        return
    _set_session_cookie(token, ADMIN_SESSION_TTL_SECONDS)


def _encode_signed_payload(payload: dict) -> str | None:
    secret = _get_secret_key()
    if not secret:
        return None

    payload_json = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload_json).decode("ascii")
    signature = hmac.new(secret.encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{signature}"


def _decode_signed_payload(token: str) -> dict | None:
    secret = _get_secret_key()
    if not secret or "." not in token:
        return None

    payload_b64, signature = token.rsplit(".", 1)
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        payload_b64.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        return None

    try:
        payload_json = base64.urlsafe_b64decode(_pad_b64(payload_b64)).decode("utf-8")
        payload = json.loads(payload_json)
    except (ValueError, json.JSONDecodeError):
        return None

    if int(payload.get("exp", 0)) <= int(time.time()):
        return None
    if not payload.get("username") or not payload.get("role"):
        return None
    return payload


def _set_session_cookie(token: str, max_age: int) -> None:
    safe_token = json.dumps(token)
    components.html(
        f"""
        <script>
        const cookieValue = "{ADMIN_SESSION_COOKIE}=" + {safe_token} + "; path=/; max-age={max_age}; SameSite=Lax";
        document.cookie = cookieValue;
        if (window.parent && window.parent.document) {{
            window.parent.document.cookie = cookieValue;
        }}
        </script>
        """,
        height=0,
    )


def _clear_session_cookie() -> None:
    components.html(
        f"""
        <script>
        const cookieValue = "{ADMIN_SESSION_COOKIE}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax";
        document.cookie = cookieValue;
        if (window.parent && window.parent.document) {{
            window.parent.document.cookie = cookieValue;
        }}
        </script>
        """,
        height=0,
    )


def _get_secret_key() -> str:
    return get_settings().streamlit_secret_key


def _pad_b64(value: str) -> str:
    return value + "=" * (-len(value) % 4)
