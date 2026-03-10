from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy.orm import Session

from app.db.base import SessionLocal


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
