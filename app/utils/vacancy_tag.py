def build_vacancy_tag(sent_vacancy_id: int | None = None, vacancy_id: int | None = None) -> str:
    if sent_vacancy_id is not None:
        return f"#VAC_{sent_vacancy_id:05d}"
    if vacancy_id is not None:
        return f"#QVAC_{vacancy_id:05d}"
    return "#VAC_00000"
