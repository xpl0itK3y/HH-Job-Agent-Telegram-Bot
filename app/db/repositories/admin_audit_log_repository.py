from sqlalchemy.orm import Session

from app.db.models.admin_audit_log import AdminAuditLog


class AdminAuditLogRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        admin_user_id: int,
        action_type: str,
        entity_type: str,
        entity_id: str,
        details_json: dict | None = None,
    ) -> AdminAuditLog:
        audit_log = AdminAuditLog(
            admin_user_id=admin_user_id,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            details_json=details_json,
        )
        self.session.add(audit_log)
        self.session.flush()
        return audit_log
