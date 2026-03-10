from bs4 import BeautifulSoup


def clean_html(html_text: str | None) -> str:
    if not html_text:
        return ""
    return BeautifulSoup(html_text, "html.parser").get_text("\n")
