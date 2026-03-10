from app.utils.pdf import extract_text_from_pdf


class _FakePage:
    def __init__(self, text: str) -> None:
        self._text = text

    def extract_text(self) -> str:
        return self._text


class _FakeReader:
    def __init__(self, _stream) -> None:
        self.pages = [_FakePage("First page"), _FakePage("Second page")]


def test_extract_text_from_pdf_reads_all_pages(monkeypatch) -> None:
    monkeypatch.setattr("app.utils.pdf.PdfReader", _FakeReader)
    result = extract_text_from_pdf(b"%PDF-fake")
    assert result == "First page\n\nSecond page"
