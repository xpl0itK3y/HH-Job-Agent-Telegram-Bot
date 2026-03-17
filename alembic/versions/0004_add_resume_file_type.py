"""Add resume file source type

Revision ID: 0004_add_resume_file
Revises: 0003_add_llm_metadata_fields
Create Date: 2026-03-17 00:00:00
"""

from alembic import op


revision = "0004_add_resume_file"
down_revision = "0003_add_llm_metadata_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE resume_source_type_enum ADD VALUE IF NOT EXISTS 'file'")


def downgrade() -> None:
    pass
