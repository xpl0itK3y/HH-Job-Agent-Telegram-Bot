from datetime import UTC, datetime
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from aiogram.types import User as TelegramUser

from app.db.models.resume import Resume, ResumeSourceType
from app.db.repositories.resume_repository import ResumeRepository
from app.db.repositories.user_repository import UserRepository
from app.db.session import session_scope
from app.integrations.deepseek.client import DeepSeekClient
from app.tasks.triggers import trigger_user_monitoring
from app.utils.pdf import extract_text_from_pdf
from app.utils.text_normalizer import normalize_text


RESUME_STORAGE_DIR = Path("storage/resumes")
RESUME_TEXT_MAX_LENGTH = 50_000


@dataclass(slots=True)
class ResumeProcessingResult:
    resume: Resume
    normalized_text: str


class ResumeService:
    def __init__(self) -> None:
        self.deepseek_client = DeepSeekClient()

    def save_text_resume(
        self,
        *,
        telegram_user: TelegramUser,
        text: str,
    ) -> ResumeProcessingResult:
        normalized_text = normalize_text(text, max_chunk_length=RESUME_TEXT_MAX_LENGTH)
        with session_scope() as session:
            user = UserRepository(session).create_or_update_telegram_user(
                telegram_user_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                language_code=telegram_user.language_code,
            )
            cached_resume = ResumeRepository(session).get_cached_by_raw_text(
                user_id=user.id,
                raw_text=text,
            )
            if cached_resume is not None and cached_resume.parsed_profile_json:
                return ResumeProcessingResult(resume=cached_resume, normalized_text=normalized_text)
            profile = self.deepseek_client.extract_resume_profile(normalized_text)
            resume = ResumeRepository(session).create(
                user_id=user.id,
                source_type=ResumeSourceType.TEXT,
                raw_text=text,
                parsed_profile_json=profile.model_dump(),
                summary=profile.summary,
                llm_prompt_version="resume_profile_v1",
                llm_model_name=self.deepseek_client.settings.deepseek_model,
                llm_generated_at=datetime.now(UTC),
            )
            telegram_user_id = user.telegram_user_id
        trigger_user_monitoring(telegram_user_id)
        return ResumeProcessingResult(resume=resume, normalized_text=normalized_text)

    def save_resume_link(
        self,
        *,
        telegram_user: TelegramUser,
        resume_link: str,
    ) -> Resume:
        with session_scope() as session:
            user = UserRepository(session).create_or_update_telegram_user(
                telegram_user_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                language_code=telegram_user.language_code,
            )
            cached_resume = ResumeRepository(session).get_cached_by_raw_text(
                user_id=user.id,
                raw_text=resume_link,
            )
            if cached_resume is not None and cached_resume.parsed_profile_json:
                return cached_resume
            profile = self.deepseek_client.extract_resume_profile(resume_link)
            resume = ResumeRepository(session).create(
                user_id=user.id,
                source_type=ResumeSourceType.LINK,
                raw_text=resume_link,
                resume_link=resume_link,
                parsed_profile_json=profile.model_dump(),
                summary=profile.summary,
                llm_prompt_version="resume_profile_v1",
                llm_model_name=self.deepseek_client.settings.deepseek_model,
                llm_generated_at=datetime.now(UTC),
            )
            telegram_user_id = user.telegram_user_id
        trigger_user_monitoring(telegram_user_id)
        return resume

    def save_pdf_resume(
        self,
        *,
        telegram_user: TelegramUser,
        filename: str,
        pdf_bytes: bytes,
    ) -> ResumeProcessingResult:
        text = extract_text_from_pdf(pdf_bytes)
        normalized_text = normalize_text(text, max_chunk_length=RESUME_TEXT_MAX_LENGTH)
        stored_path = self._store_resume_file(telegram_user.id, filename, pdf_bytes)

        with session_scope() as session:
            user = UserRepository(session).create_or_update_telegram_user(
                telegram_user_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                language_code=telegram_user.language_code,
            )
            cached_resume = ResumeRepository(session).get_cached_by_raw_text(
                user_id=user.id,
                raw_text=text,
            )
            if cached_resume is not None and cached_resume.parsed_profile_json:
                return ResumeProcessingResult(resume=cached_resume, normalized_text=normalized_text)
            profile = self.deepseek_client.extract_resume_profile(normalized_text)
            resume = ResumeRepository(session).create(
                user_id=user.id,
                source_type=ResumeSourceType.PDF,
                file_path=str(stored_path),
                raw_text=text,
                parsed_profile_json=profile.model_dump(),
                summary=profile.summary,
                llm_prompt_version="resume_profile_v1",
                llm_model_name=self.deepseek_client.settings.deepseek_model,
                llm_generated_at=datetime.now(UTC),
            )
            telegram_user_id = user.telegram_user_id
        trigger_user_monitoring(telegram_user_id)
        return ResumeProcessingResult(resume=resume, normalized_text=normalized_text)

    def _store_resume_file(self, telegram_user_id: int, filename: str, pdf_bytes: bytes) -> Path:
        RESUME_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = Path(filename).name or "resume.pdf"
        stored_path = RESUME_STORAGE_DIR / f"{telegram_user_id}_{uuid4().hex}_{safe_name}"
        stored_path.write_bytes(pdf_bytes)
        return stored_path
