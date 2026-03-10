import re


MULTISPACE_RE = re.compile(r"[ \t]+")
MULTIBREAK_RE = re.compile(r"\n{3,}")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


def normalize_text(text: str, max_chunk_length: int = 2000) -> str:
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = CONTROL_RE.sub("", cleaned)
    lines = [MULTISPACE_RE.sub(" ", line).strip() for line in cleaned.split("\n")]
    cleaned = "\n".join(line for line in lines if line)
    cleaned = MULTIBREAK_RE.sub("\n\n", cleaned).strip()
    if len(cleaned) <= max_chunk_length:
        return cleaned
    return cleaned[:max_chunk_length].rstrip() + "..."
