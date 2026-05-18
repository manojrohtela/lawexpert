from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from collections import Counter

from .config import DATASET_DIR, PROCESSED_DIR, settings
from .llm_client import GroqClient, extract_json_object
from .models import CaseRecord
from .pdf_utils import extract_pdf_text, normalize_whitespace, stable_slug


YEAR_RE = re.compile(r"/(\d{4})/")


def infer_case_name(pdf_path: Path) -> str:
    stem = pdf_path.stem.replace("_", " ")
    stem = re.sub(r"\s+\(\d+\)$", "", stem)
    stem = re.sub(r"\s+on\s+\d{1,2}\s+[A-Za-z]+\s+\d{4}.*$", "", stem, flags=re.I)
    return normalize_whitespace(stem)


def infer_year_from_path(pdf_path: Path) -> int:
    match = YEAR_RE.search(str(pdf_path))
    if match:
        return int(match.group(1))
    return 0


def estimate_court(text: str, path: Path) -> str:
    lower = text.lower()
    if "supreme court" in lower:
        return "Supreme Court of India"
    if "high court" in lower:
        return "High Court"
    if "tribunal" in lower:
        return "Tribunal"
    if "district court" in lower:
        return "District Court"
    return "Unknown Court"


def quality_score(text: str) -> float:
    if not text:
        return 0.0
    char_count = len(text)
    word_count = len(text.split())
    unique_ratio = len(set(text.lower().split())) / max(word_count, 1)
    digit_penalty = text.count("�") + text.count("\x00")
    return (word_count / 1000.0) + unique_ratio - (digit_penalty * 0.2) + (char_count / 10000.0)


def fingerprint(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def normalize_multiline_text(text: str) -> str:
    lines = [normalize_whitespace(line) for line in str(text).splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines).strip()


def parse_case_summary(raw: str, source_file: str, year: int) -> dict:
    try:
        payload = extract_json_object(raw)
    except Exception:
        payload = {}

    case_name = payload.get("case_name") or infer_case_name(Path(source_file))
    summary = payload.get("summary") or raw.strip()
    if isinstance(summary, list):
        summary = "\n".join(map(str, summary))

    relevant_sections = payload.get("relevant_sections") or []
    if isinstance(relevant_sections, str):
        relevant_sections = [relevant_sections]

    return {
        "case_name": normalize_whitespace(str(case_name)),
        "year": int(payload.get("year") or year or 0),
        "court": normalize_whitespace(str(payload.get("court") or "Unknown Court")),
        "summary": normalize_multiline_text(str(summary)),
        "key_legal_point": normalize_whitespace(
            str(payload.get("key_legal_point") or "Not explicitly stated in the document.")
        ),
        "relevant_sections": [normalize_whitespace(str(x)) for x in relevant_sections if str(x).strip()],
        "topic": normalize_whitespace(str(payload.get("topic") or "General")),
    }


def generate_case_metadata(pdf_text: str, source_file: str, year: int, client: GroqClient) -> dict:
    if not client.available():
        return local_case_metadata(pdf_text, source_file, year)

    prompt = f"""
You are a legal analyst. Extract a compact structured summary from the case law text below.
Return ONLY valid JSON with these keys:
case_name, year, court, summary, key_legal_point, relevant_sections, topic

Rules:
- summary must be 5 to 8 lines, concise and factual.
- relevant_sections should be an array of legal sections/articles if they appear in the text.
- topic should be a short subject label.
- If a field is unknown, use a sensible short placeholder.

Source file: {source_file}
Year: {year}

CASE TEXT:
{pdf_text[:22000]}
""".strip()

    raw = client.chat(
        [
            {
                "role": "system",
                "content": "You produce strictly valid JSON and nothing else.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
    )
    parsed = parse_case_summary(raw, source_file, year)
    if parsed.get("case_name") == "Unknown Case" or "LLM unavailable" in parsed.get("summary", ""):
        return local_case_metadata(pdf_text, source_file, year)
    return parsed


def local_case_metadata(pdf_text: str, source_file: str, year: int) -> dict:
    case_name = infer_case_name(Path(source_file))
    court = estimate_court(pdf_text, Path(source_file))
    paragraphs = [part.strip() for part in re.split(r"\n{2,}", pdf_text) if part.strip()]
    lead = paragraphs[:4]
    if not lead:
        lead = [pdf_text[:1200]]

    sentences = re.split(r"(?<=[.!?])\s+", " ".join(lead))
    summary_lines = []
    for sentence in sentences[:8]:
        cleaned = normalize_whitespace(sentence)
        if cleaned:
            summary_lines.append(cleaned)
    summary = "\n".join(summary_lines[:6]) or normalize_whitespace(pdf_text[:800])

    keywords = Counter(
        token
        for token in re.findall(r"[A-Za-z]{4,}", pdf_text.lower())
        if token
        not in {
            "court",
            "appeal",
            "judge",
            "judgment",
            "order",
            "state",
            "respondent",
            "appellant",
            "petition",
            "section",
            "article",
            "india",
            "legal",
        }
    )
    topic = keywords.most_common(1)[0][0].title() if keywords else "General"
    relevant_sections = sorted(set(re.findall(r"\b(?:section|article)\s+\d+[A-Za-z0-9().\-\/]*", pdf_text, flags=re.I)))
    key_legal_point = (
        summary_lines[0]
        if summary_lines
        else "The case turns on the facts and legal reasoning contained in the judgment."
    )

    return {
        "case_name": case_name,
        "year": year or infer_year_from_path(Path(source_file)),
        "court": court,
        "summary": summary,
        "key_legal_point": key_legal_point,
        "relevant_sections": relevant_sections[:8],
        "topic": topic,
    }


def build_cases_dataset(limit: int | None = None) -> list[dict]:
    client = GroqClient()
    records: list[dict] = []
    seen_fingerprints: set[str] = set()
    seen_case_keys: set[str] = set()

    year_dirs = sorted([p for p in DATASET_DIR.iterdir() if p.is_dir() and p.name.isdigit()])
    processed = 0
    for year_dir in year_dirs:
        all_pdfs = sorted(p for p in year_dir.iterdir() if p.suffix.lower() == ".pdf")
        for pdf_file in all_pdfs:
            if limit and processed >= limit:
                return records

            text = extract_pdf_text(pdf_file)
            if len(text) < settings.min_case_chars:
                continue
            if quality_score(text) < 0.75:
                continue

            text_fp = fingerprint(text[:12000])
            case_name_guess = stable_slug(infer_case_name(pdf_file))
            if text_fp in seen_fingerprints or case_name_guess in seen_case_keys:
                continue

            metadata = generate_case_metadata(text, str(pdf_file), int(year_dir.name), client)
            metadata["source_file"] = str(pdf_file)
            metadata["year"] = metadata.get("year") or int(year_dir.name)
            metadata["court"] = metadata.get("court") or estimate_court(text, pdf_file)

            case_fp = stable_slug(metadata["case_name"] + " " + str(metadata["year"]))
            summary_fp = fingerprint(metadata["summary"])
            if case_fp in seen_case_keys or summary_fp in seen_fingerprints:
                continue

            seen_fingerprints.add(text_fp)
            seen_fingerprints.add(summary_fp)
            seen_case_keys.update({case_name_guess, case_fp})

            records.append(CaseRecord(**metadata).model_dump())
            processed += 1

    return records


def save_cases_dataset(records: list[dict], output_path: Path | None = None) -> Path:
    output_path = output_path or (PROCESSED_DIR / "cases.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def process_cases(limit: int | None = None) -> Path:
    records = build_cases_dataset(limit=limit)
    return save_cases_dataset(records)
