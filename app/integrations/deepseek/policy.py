from enum import StrEnum


class LLMUsageMode(StrEnum):
    NO_LLM = "no_llm"
    LLM_ONCE = "llm_once"
    LLM_LIVE = "llm_live"


LLM_OPERATION_MODES = {
    "resume_profile_extraction": LLMUsageMode.LLM_ONCE,
    "vacancy_description_summary": LLMUsageMode.LLM_ONCE,
    "vacancy_match_analysis": LLMUsageMode.LLM_ONCE,
    "cover_letter_generation": LLMUsageMode.LLM_ONCE,
    "vacancy_chat_qa": LLMUsageMode.LLM_LIVE,
    "html_cleanup": LLMUsageMode.NO_LLM,
    "vacancy_deduplication": LLMUsageMode.NO_LLM,
    "employer_score": LLMUsageMode.NO_LLM,
}


def get_operation_mode(operation_name: str) -> LLMUsageMode:
    return LLM_OPERATION_MODES[operation_name]
