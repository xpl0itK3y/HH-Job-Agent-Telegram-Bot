"""Initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-03-10 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


bot_status_enum = sa.Enum("active", "paused", name="bot_status_enum")
resume_source_type_enum = sa.Enum("pdf", "text", "link", name="resume_source_type_enum")
chat_message_role_enum = sa.Enum("user", "assistant", "system", name="chat_message_role_enum")
admin_role_enum = sa.Enum("admin", "viewer", name="admin_role_enum")


def upgrade() -> None:
    bot_status_enum.create(op.get_bind(), checkfirst=True)
    resume_source_type_enum.create(op.get_bind(), checkfirst=True)
    chat_message_role_enum.create(op.get_bind(), checkfirst=True)
    admin_role_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "admin_users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("role", admin_role_enum, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_admin_users")),
        sa.UniqueConstraint("username", name=op.f("uq_admin_users_username")),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("last_name", sa.String(length=255), nullable=True),
        sa.Column("language_code", sa.String(length=16), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("bot_status", bot_status_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("telegram_user_id", name=op.f("uq_users_telegram_user_id")),
    )
    op.create_table(
        "vacancies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("hh_vacancy_id", sa.String(length=64), nullable=False),
        sa.Column("employer_hh_id", sa.String(length=64), nullable=True),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("company_name", sa.String(length=512), nullable=False),
        sa.Column("salary_from", sa.Integer(), nullable=True),
        sa.Column("salary_to", sa.Integer(), nullable=True),
        sa.Column("salary_currency", sa.String(length=16), nullable=True),
        sa.Column("employment_type", sa.String(length=128), nullable=True),
        sa.Column("work_format", sa.String(length=128), nullable=True),
        sa.Column("experience", sa.String(length=128), nullable=True),
        sa.Column("area_name", sa.String(length=255), nullable=True),
        sa.Column("description_raw", sa.Text(), nullable=True),
        sa.Column("description_clean", sa.Text(), nullable=True),
        sa.Column("description_ai_summary", sa.Text(), nullable=True),
        sa.Column("key_skills_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("alternate_url", sa.String(length=2048), nullable=True),
        sa.Column("source_country_code", sa.String(length=2), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_vacancies")),
    )
    op.create_table(
        "admin_audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("admin_user_id", sa.Integer(), nullable=False),
        sa.Column("action_type", sa.String(length=128), nullable=False),
        sa.Column("entity_type", sa.String(length=128), nullable=False),
        sa.Column("entity_id", sa.String(length=128), nullable=False),
        sa.Column("details_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["admin_user_id"], ["admin_users.id"], name=op.f("fk_admin_audit_logs_admin_user_id_admin_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_admin_audit_logs")),
    )
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("vacancy_id", sa.Integer(), nullable=False),
        sa.Column("role", chat_message_role_enum, nullable=False),
        sa.Column("message_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_chat_messages_user_id_users")),
        sa.ForeignKeyConstraint(["vacancy_id"], ["vacancies.id"], name=op.f("fk_chat_messages_vacancy_id_vacancies")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chat_messages")),
    )
    op.create_table(
        "resumes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("source_type", resume_source_type_enum, nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=True),
        sa.Column("resume_link", sa.String(length=2048), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("parsed_profile_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_resumes_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_resumes")),
    )
    op.create_table(
        "scheduled_reminders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("reminder_type", sa.String(length=128), nullable=False),
        sa.Column("run_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_scheduled_reminders_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_scheduled_reminders")),
    )
    op.create_table(
        "search_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("keywords", sa.String(length=512), nullable=True),
        sa.Column("selected_countries_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("area_ids_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("employment_type", sa.String(length=128), nullable=True),
        sa.Column("work_format", sa.String(length=128), nullable=True),
        sa.Column("professional_role", sa.String(length=255), nullable=True),
        sa.Column("search_extra_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_search_settings_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_search_settings")),
    )
    op.create_table(
        "sent_vacancies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("vacancy_id", sa.Integer(), nullable=False),
        sa.Column("vacancy_tag", sa.String(length=64), nullable=False),
        sa.Column("match_score", sa.Integer(), nullable=True),
        sa.Column("match_summary", sa.Text(), nullable=True),
        sa.Column("missing_skills_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("employer_check_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("cover_letter", sa.Text(), nullable=True),
        sa.Column("telegram_message_id", sa.String(length=128), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_sent_vacancies_user_id_users")),
        sa.ForeignKeyConstraint(["vacancy_id"], ["vacancies.id"], name=op.f("fk_sent_vacancies_vacancy_id_vacancies")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sent_vacancies")),
        sa.UniqueConstraint("user_id", "vacancy_id", name="uq_sent_vacancy_user_vacancy"),
        sa.UniqueConstraint("vacancy_tag", name=op.f("uq_sent_vacancies_vacancy_tag")),
    )

    op.create_index(op.f("ix_admin_audit_logs_admin_user_id"), "admin_audit_logs", ["admin_user_id"], unique=False)
    op.create_index(op.f("ix_chat_messages_user_id"), "chat_messages", ["user_id"], unique=False)
    op.create_index(op.f("ix_chat_messages_vacancy_id"), "chat_messages", ["vacancy_id"], unique=False)
    op.create_index(op.f("ix_resumes_user_id"), "resumes", ["user_id"], unique=False)
    op.create_index(op.f("ix_scheduled_reminders_run_at"), "scheduled_reminders", ["run_at"], unique=False)
    op.create_index(op.f("ix_scheduled_reminders_user_id"), "scheduled_reminders", ["user_id"], unique=False)
    op.create_index(op.f("ix_search_settings_user_id"), "search_settings", ["user_id"], unique=False)
    op.create_index(op.f("ix_sent_vacancies_user_id"), "sent_vacancies", ["user_id"], unique=False)
    op.create_index(op.f("ix_sent_vacancies_vacancy_id"), "sent_vacancies", ["vacancy_id"], unique=False)
    op.create_index(op.f("ix_users_telegram_user_id"), "users", ["telegram_user_id"], unique=True)
    op.create_index(op.f("ix_vacancies_employer_hh_id"), "vacancies", ["employer_hh_id"], unique=False)
    op.create_index(op.f("ix_vacancies_hh_vacancy_id"), "vacancies", ["hh_vacancy_id"], unique=False)
    op.create_index(op.f("ix_vacancies_provider"), "vacancies", ["provider"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_vacancies_provider"), table_name="vacancies")
    op.drop_index(op.f("ix_vacancies_hh_vacancy_id"), table_name="vacancies")
    op.drop_index(op.f("ix_vacancies_employer_hh_id"), table_name="vacancies")
    op.drop_index(op.f("ix_users_telegram_user_id"), table_name="users")
    op.drop_index(op.f("ix_sent_vacancies_vacancy_id"), table_name="sent_vacancies")
    op.drop_index(op.f("ix_sent_vacancies_user_id"), table_name="sent_vacancies")
    op.drop_index(op.f("ix_search_settings_user_id"), table_name="search_settings")
    op.drop_index(op.f("ix_scheduled_reminders_user_id"), table_name="scheduled_reminders")
    op.drop_index(op.f("ix_scheduled_reminders_run_at"), table_name="scheduled_reminders")
    op.drop_index(op.f("ix_resumes_user_id"), table_name="resumes")
    op.drop_index(op.f("ix_chat_messages_vacancy_id"), table_name="chat_messages")
    op.drop_index(op.f("ix_chat_messages_user_id"), table_name="chat_messages")
    op.drop_index(op.f("ix_admin_audit_logs_admin_user_id"), table_name="admin_audit_logs")

    op.drop_table("sent_vacancies")
    op.drop_table("search_settings")
    op.drop_table("scheduled_reminders")
    op.drop_table("resumes")
    op.drop_table("chat_messages")
    op.drop_table("admin_audit_logs")
    op.drop_table("vacancies")
    op.drop_table("users")
    op.drop_table("admin_users")

    admin_role_enum.drop(op.get_bind(), checkfirst=True)
    chat_message_role_enum.drop(op.get_bind(), checkfirst=True)
    resume_source_type_enum.drop(op.get_bind(), checkfirst=True)
    bot_status_enum.drop(op.get_bind(), checkfirst=True)
