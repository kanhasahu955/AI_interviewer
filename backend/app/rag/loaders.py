"""Document loaders: PDF + DOCX + plain text -> string."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("app.rag.loaders")


def load_pdf(path: str | Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception as exc:
            logger.warning("Failed to extract a PDF page: %s", exc)
    return "\n".join(parts).strip()


def load_docx(path: str | Path) -> str:
    from docx import Document

    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs).strip()


def load_text_file(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8", errors="ignore")


def load_document(path: str | Path) -> str:
    """Dispatch loader based on file extension."""
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".pdf":
        return load_pdf(p)
    if suffix in {".docx", ".doc"}:
        return load_docx(p)
    if suffix in {".txt", ".md", ".rst"}:
        return load_text_file(p)
    return load_text_file(p)
