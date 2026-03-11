"""Add llm metadata fields

Revision ID: 0003_add_llm_metadata_fields
Revises: 0002_sent_vacancy_proc
Create Date: 2026-03-10 01:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_add_llm_metadata_fields"
down_revision = "0002_sent_vacancy_proc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table_name in ("resumes", "vacancies", "sent_vacancies"):
        op.add_column(table_name, sa.Column("llm_prompt_version", sa.String(length=64), nullable=True))
        op.add_column(table_name, sa.Column("llm_model_name", sa.String(length=128), nullable=True))
        op.add_column(table_name, sa.Column("llm_generated_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    for table_name in ("sent_vacancies", "vacancies", "resumes"):
        op.drop_column(table_name, "llm_generated_at")
        op.drop_column(table_name, "llm_model_name")
        op.drop_column(table_name, "llm_prompt_version")
