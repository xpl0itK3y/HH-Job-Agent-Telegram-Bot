from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ResumeProfileSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    position: str | None = None
    seniority: str | None = None
    primary_stack: list[str] = Field(default_factory=list)
    secondary_stack: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    years_experience: int | None = None
    english_level: str | None = None
    summary: str | None = None
    status: str = "ok"
    error: str | None = None


class VacancyAnalysisSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    match_score: int = 0
    match_summary: str = ""
    missing_skills: list[str] = Field(default_factory=list)


class CoverLetterSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    cover_letter: str = ""


class ChatCompletionMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatCompletionMessage]
    temperature: float = 0.1
    response_format: dict[str, str] | None = None


class ChatCompletionResponse(BaseModel):
    choices: list[dict[str, Any]]
