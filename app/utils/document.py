from __future__ import annotations

import re
from html import unescape
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from app.utils.html_cleaner import clean_html
from app.utils.pdf import extract_text_from_pdf


class UnsupportedDocumentFormatError(ValueError):
    pass


SUPPORTED_RESUME_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".md",
    ".html",
    ".htm",
    ".rtf",
    ".docx",
    ".odt",
}

_RTF_CONTROL_WORD_RE = re.compile(r"\\[a-zA-Z]+-?\d* ?")
_RTF_HEX_RE = re.compile(r"\\'([0-9a-fA-F]{2})")
_RTF_GROUP_RE = re.compile(r"[{}]")
_WHITESPACE_RE = re.compile(r"[ \t]+")


def extract_text_from_document(*, filename: str, mime_type: str | None, file_bytes: bytes) -> str:
    extension = Path(filename).suffix.lower()

    if extension == ".pdf" or mime_type == "application/pdf":
        return extract_text_from_pdf(file_bytes)
    if extension in {".txt", ".md"}:
        return _decode_text(file_bytes)
    if extension in {".html", ".htm"}:
        return clean_html(_decode_text(file_bytes))
    if extension == ".rtf":
        return _extract_text_from_rtf(file_bytes)
    if extension == ".docx":
        return _extract_text_from_docx(file_bytes)
    if extension == ".odt":
        return _extract_text_from_odt(file_bytes)
    if extension == ".doc":
        raise UnsupportedDocumentFormatError(
            "Формат .doc не поддерживается. Сохраните файл как .docx, .pdf, .txt, .rtf или .odt."
        )
    raise UnsupportedDocumentFormatError(
        "Неподдерживаемый формат файла. Поддерживаются: pdf, docx, odt, txt, md, html, rtf."
    )


def _decode_text(file_bytes: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "cp1251", "latin-1"):
        try:
            return file_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    return file_bytes.decode("utf-8", errors="ignore")


def _extract_text_from_docx(file_bytes: bytes) -> str:
    with ZipFile(BytesIO(file_bytes)) as archive:
        xml_text = archive.read("word/document.xml").decode("utf-8")
    xml_text = re.sub(r"</w:p>", "\n", xml_text)
    xml_text = re.sub(r"<[^>]+>", "", xml_text)
    return unescape(xml_text).strip()


def _extract_text_from_odt(file_bytes: bytes) -> str:
    with ZipFile(BytesIO(file_bytes)) as archive:
        xml_text = archive.read("content.xml").decode("utf-8")
    xml_text = re.sub(r"</text:p>", "\n", xml_text)
    xml_text = re.sub(r"<text:tab[^>]*\/>", "\t", xml_text)
    xml_text = re.sub(r"<[^>]+>", "", xml_text)
    return unescape(xml_text).strip()


def _extract_text_from_rtf(file_bytes: bytes) -> str:
    text = _decode_text(file_bytes)

    def _hex_replace(match: re.Match[str]) -> str:
        try:
            return bytes.fromhex(match.group(1)).decode("cp1251")
        except Exception:
            return ""

    text = _RTF_HEX_RE.sub(_hex_replace, text)
    text = text.replace("\\par", "\n")
    text = _RTF_CONTROL_WORD_RE.sub("", text)
    text = _RTF_GROUP_RE.sub("", text)
    text = text.replace("\\", "")
    text = unescape(text)
    lines = [_WHITESPACE_RE.sub(" ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()
