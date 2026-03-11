"""Add sent vacancy processing fields

Revision ID: 0002_sent_vacancy_proc
Revises: 0001_initial_schema
Create Date: 2026-03-10 00:30:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_sent_vacancy_proc"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


processing_status_enum = sa.dialects.postgresql.ENUM(
    "queued",
    "processing",
    "ready_to_send",
    "sent",
    "failed",
    name="processing_status_enum",
    create_type=False,
)
pipeline_step_enum = sa.dialects.postgresql.ENUM(
    "cleaning",
    "ai_summary",
    "employer_check",
    "match_analysis",
    "cover_letter",
    "card_generation",
    "ready_to_send",
    name="pipeline_step_enum",
    create_type=False,
)


def upgrade() -> None:
    processing_status_enum.create(op.get_bind(), checkfirst=True)
    pipeline_step_enum.create(op.get_bind(), checkfirst=True)

    op.add_column("sent_vacancies", sa.Column("processing_status", processing_status_enum, nullable=True))
    op.add_column("sent_vacancies", sa.Column("current_pipeline_step", pipeline_step_enum, nullable=True))
    op.add_column("sent_vacancies", sa.Column("last_error_text", sa.Text(), nullable=True))
    op.add_column("sent_vacancies", sa.Column("retry_count", sa.Integer(), nullable=True))
    op.add_column("sent_vacancies", sa.Column("queued_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("sent_vacancies", sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("sent_vacancies", sa.Column("ready_to_send_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("sent_vacancies", sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE sent_vacancies SET processing_status = 'queued', retry_count = 0 WHERE processing_status IS NULL")
    op.alter_column("sent_vacancies", "processing_status", nullable=False)
    op.alter_column("sent_vacancies", "retry_count", nullable=False)


def downgrade() -> None:
    op.drop_column("sent_vacancies", "failed_at")
    op.drop_column("sent_vacancies", "ready_to_send_at")
    op.drop_column("sent_vacancies", "processing_started_at")
    op.drop_column("sent_vacancies", "queued_at")
    op.drop_column("sent_vacancies", "retry_count")
    op.drop_column("sent_vacancies", "last_error_text")
    op.drop_column("sent_vacancies", "current_pipeline_step")
    op.drop_column("sent_vacancies", "processing_status")
    pipeline_step_enum.drop(op.get_bind(), checkfirst=True)
    processing_status_enum.drop(op.get_bind(), checkfirst=True)
