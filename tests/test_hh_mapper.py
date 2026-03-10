from app.integrations.hh.config import get_provider_config
from app.integrations.hh.mapper import map_hh_vacancy


def test_map_hh_vacancy_normalizes_fields() -> None:
    raw = {
        "id": "123",
        "name": "Python Developer",
        "alternate_url": "https://hh.kz/vacancy/123",
        "description": "<p>Desc</p>",
        "published_at": "2026-03-10T10:00:00+03:00",
        "salary": {"from": 1000, "to": 2000, "currency": "USD"},
        "employer": {"id": "77", "name": "ACME"},
        "area": {"name": "Almaty"},
        "experience": {"id": "between1And3", "name": "1-3 years"},
        "employment": {"id": "full", "name": "Full"},
        "schedule": {"id": "remote", "name": "Remote"},
        "key_skills": [{"name": "Python"}, {"name": "FastAPI"}],
    }
    mapped = map_hh_vacancy(raw, get_provider_config("KZ"))
    assert mapped["provider"] == "hh_kz"
    assert mapped["source_country_code"] == "KZ"
    assert mapped["hh_vacancy_id"] == "123"
    assert mapped["company_name"] == "ACME"
    assert mapped["key_skills_json"] == ["Python", "FastAPI"]
