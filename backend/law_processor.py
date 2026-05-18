from __future__ import annotations

import json
import re
from pathlib import Path

from .config import DOCS_DIR, PROCESSED_DIR
from .models import LawRecord
from .pdf_utils import clean_text, extract_pdf_text


LAW_NAME_MAP = {
    "bns": "BNS",
    "bnss": "BNSS",
    "bsa": "BSA",
    "ipc": "IPC",
    "constitution": "Constitution",
    "constituion": "Constitution",
    "itact": "IT Act",
    "it_act": "IT Act",
    "narcotics": "NDPS",
    "ndps": "NDPS",
    "motoract": "Motor Vehicles Act",
    "motor_vehicles": "Motor Vehicles Act",
    "pca": "PCA",
}


# Matches: "Section 302", "Article 21"
_WORD_HEADER_RE = re.compile(
    r"(?im)^[ \t]*(section|article)[ \t]+([0-9][0-9A-Za-z()\.\-\/]*)[ \t]*[.:]?[ \t]*$"
)
# Matches BNS/IPC-style: "302." or "302A." or "103.(1)" at start of line
_NUM_HEADER_RE = re.compile(
    r"(?m)^[ \t]*([0-9]{1,3}[A-Z]?)\.(?:\([0-9]+\))?[ \t]+(?=[A-Z(])"
)


def infer_law_name(pdf_path: Path) -> str:
    stem = pdf_path.stem.lower()
    for key, name in LAW_NAME_MAP.items():
        if key in stem:
            return name
    return pdf_path.stem


def split_by_sections(text: str, law_name: str = "") -> list[tuple[str, str]]:
    # For BNS/IPC style (numbered sections like "103. Punishment for murder")
    # prefer the numeric header pattern which is more accurate
    use_numeric = law_name in ("BNS", "IPC", "NDPS", "PCA")

    raw_matches: list[tuple[int, str]] = []

    if use_numeric:
        for m in _NUM_HEADER_RE.finditer(text):
            raw_matches.append((m.start(), f"Section {m.group(1)}"))
        # Fall back to word-style if numeric found nothing
        if not raw_matches:
            for m in _WORD_HEADER_RE.finditer(text):
                raw_matches.append((m.start(), f"{m.group(1).capitalize()} {m.group(2).strip()}"))
    else:
        for m in _WORD_HEADER_RE.finditer(text):
            raw_matches.append((m.start(), f"{m.group(1).capitalize()} {m.group(2).strip()}"))
        if not raw_matches:
            for m in _NUM_HEADER_RE.finditer(text):
                raw_matches.append((m.start(), f"Section {m.group(1)}"))

    raw_matches.sort(key=lambda x: x[0])
    chunks: list[tuple[str, str]] = []
    for idx, (start, label) in enumerate(raw_matches):
        end = raw_matches[idx + 1][0] if idx + 1 < len(raw_matches) else len(text)
        chunk_text = clean_text(text[start:end])
        if len(chunk_text) > 30:
            chunks.append((label, chunk_text))
    return chunks


def build_laws_dataset() -> list[dict]:
    records: list[dict] = []
    pdf_files = sorted(p for p in DOCS_DIR.iterdir() if p.suffix.lower() == ".pdf")
    for pdf_file in pdf_files:
        law_name = infer_law_name(pdf_file)
        text = extract_pdf_text(pdf_file)
        if not text:
            continue
        chunks = split_by_sections(text, law_name)
        if not chunks:
            fallback = LawRecord(
                text=text[:10000],
                law_name=law_name,
                section_or_article="Unknown",
            )
            records.append(fallback.model_dump())
            continue
        for section_or_article, chunk_text in chunks:
            records.append(
                LawRecord(
                    text=chunk_text,
                    law_name=law_name,
                    section_or_article=section_or_article,
                ).model_dump()
            )
    return records


def save_laws_dataset(records: list[dict], output_path: Path | None = None) -> Path:
    output_path = output_path or (PROCESSED_DIR / "laws.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def process_laws() -> Path:
    records = build_laws_dataset()
    return save_laws_dataset(records)
