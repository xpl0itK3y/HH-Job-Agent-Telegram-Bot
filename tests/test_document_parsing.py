from io import BytesIO
from zipfile import ZipFile

import pytest

from app.utils.document import UnsupportedDocumentFormatError, extract_text_from_document


def test_extract_text_from_txt_document() -> None:
    result = extract_text_from_document(
        filename="resume.txt",
        mime_type="text/plain",
        file_bytes="Python\nBackend".encode("utf-8"),
    )
    assert result == "Python\nBackend"


def test_extract_text_from_docx_document() -> None:
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr(
            "word/document.xml",
            (
                "<w:document><w:body>"
                "<w:p><w:r><w:t>Python</w:t></w:r></w:p>"
                "<w:p><w:r><w:t>FastAPI</w:t></w:r></w:p>"
                "</w:body></w:document>"
            ),
        )
    result = extract_text_from_document(
        filename="resume.docx",
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        file_bytes=buffer.getvalue(),
    )
    assert result == "Python\nFastAPI"


def test_extract_text_from_rtf_document() -> None:
    result = extract_text_from_document(
        filename="resume.rtf",
        mime_type="application/rtf",
        file_bytes=rb"{\rtf1\ansi Python\par FastAPI}",
    )
    assert result == "Python\nFastAPI"


def test_unsupported_doc_format_raises() -> None:
    with pytest.raises(UnsupportedDocumentFormatError):
        extract_text_from_document(
            filename="resume.doc",
            mime_type="application/msword",
            file_bytes=b"binary-doc",
        )
