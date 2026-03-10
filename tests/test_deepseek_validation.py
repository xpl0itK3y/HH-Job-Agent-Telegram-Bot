import json

from app.integrations.deepseek.client import DeepSeekClient


def test_extract_resume_profile_validates_json(monkeypatch) -> None:
    client = DeepSeekClient()
    client.settings.deepseek_api_key = "token"
    client.settings.deepseek_base_url = "https://example.com"

    payload = {
        "position": "Python Developer",
        "seniority": "middle",
        "primary_stack": ["Python"],
        "secondary_stack": ["FastAPI"],
        "domains": ["Backend"],
        "years_experience": 3,
        "english_level": "B1",
        "summary": "Summary",
    }

    monkeypatch.setattr(client, "_chat_completion", lambda _: json.dumps(payload))
    result = client.extract_resume_profile("resume text")
    assert result.position == "Python Developer"
    assert result.status == "ok"


def test_extract_resume_profile_returns_needs_review_on_invalid_json(monkeypatch) -> None:
    client = DeepSeekClient()
    client.settings.deepseek_api_key = "token"
    client.settings.deepseek_base_url = "https://example.com"

    monkeypatch.setattr(client, "_chat_completion", lambda _: "{invalid json")
    result = client.extract_resume_profile("resume text")
    assert result.status == "needs_review"
