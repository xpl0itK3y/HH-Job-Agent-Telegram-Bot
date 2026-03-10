from app.utils.vacancy_tag import build_vacancy_tag


def test_build_vacancy_tag_from_sent_vacancy_id() -> None:
    assert build_vacancy_tag(sent_vacancy_id=17) == "#VAC_00017"


def test_build_vacancy_tag_from_vacancy_id() -> None:
    assert build_vacancy_tag(vacancy_id=321) == "#VAC_00321"
