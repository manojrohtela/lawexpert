from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable


def extract_pdf_text(pdf_path: str | Path) -> str:
    path = Path(pdf_path)
    text_parts: list[str] = []

    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(path))
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text:
                text_parts.append(page_text)
    except Exception:
        try:
            from PyPDF2 import PdfReader  # type: ignore

            reader = PdfReader(str(path))
            for page in reader.pages:
                page_text = page.extract_text() or ""
                if page_text:
                    text_parts.append(page_text)
        except Exception:
            try:
                import fitz  # type: ignore

                doc = fitz.open(str(path))
                for page in doc:
                    page_text = page.get_text()
                    if page_text:
                        text_parts.append(page_text)
            except Exception:
                raw = path.read_bytes()
                text_parts.append(raw.decode("utf-8", errors="ignore"))

    return clean_text("\n".join(text_parts))


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"-\n(?=[a-z])", "", text)
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines).strip()


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def stable_slug(text: str) -> str:
    text = normalize_whitespace(text).lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_")

