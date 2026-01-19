from __future__ import annotations

from pathlib import Path

from PyPDF2 import PdfReader


def extract_pdf_text(path: str | Path, max_chars: int | None = 20000) -> str:
    """
    Извлекает текст из PDF. Чтобы не слать в LLM слишком большие документы,
    можно ограничить длину max_chars.
    """
    p = Path(path)
    reader = PdfReader(str(p))
    chunks: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if not text:
            continue
        chunks.append(text)
        joined = "\n\n".join(chunks)
        if max_chars is not None and len(joined) >= max_chars:
            return joined[:max_chars]
    return "\n\n".join(chunks)


