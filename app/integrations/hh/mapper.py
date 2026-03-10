from datetime import datetime
from typing import Any

from app.integrations.hh.config import HHProviderConfig


def map_hh_vacancy(raw_vacancy: dict[str, Any], config: HHProviderConfig) -> dict[str, Any]:
    salary = raw_vacancy.get("salary") or {}
    employer = raw_vacancy.get("employer") or {}
    area = raw_vacancy.get("area") or {}
    experience = raw_vacancy.get("experience") or {}
    employment = raw_vacancy.get("employment") or {}
    schedule = raw_vacancy.get("schedule") or {}
    key_skills = raw_vacancy.get("key_skills") or []

    return {
        "provider": config.provider,
        "hh_vacancy_id": str(raw_vacancy["id"]),
        "employer_hh_id": _safe_id(employer.get("id")),
        "title": raw_vacancy.get("name") or "Untitled vacancy",
        "company_name": employer.get("name") or "Unknown company",
        "salary_from": salary.get("from"),
        "salary_to": salary.get("to"),
        "salary_currency": salary.get("currency"),
        "employment_type": employment.get("id") or employment.get("name"),
        "work_format": schedule.get("id") or schedule.get("name"),
        "experience": experience.get("id") or experience.get("name"),
        "area_name": area.get("name"),
        "description_raw": raw_vacancy.get("description"),
        "description_clean": None,
        "description_ai_summary": None,
        "key_skills_json": [item.get("name") for item in key_skills if item.get("name")],
        "alternate_url": raw_vacancy.get("alternate_url"),
        "source_country_code": config.country_code,
        "published_at": _parse_datetime(raw_vacancy.get("published_at")),
        "fetched_at": datetime.utcnow(),
    }


def _safe_id(value: Any) -> str | None:
    return str(value) if value is not None else None


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None
