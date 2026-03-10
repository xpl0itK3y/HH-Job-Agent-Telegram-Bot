from app.utils.html_cleaner import clean_html


def test_clean_html_strips_tags() -> None:
    html = "<div><p>Hello <b>world</b></p><p>Next</p></div>"
    cleaned = clean_html(html)
    assert "Hello" in cleaned
    assert "world" in cleaned
    assert "Next" in cleaned
    assert "<b>" not in cleaned
