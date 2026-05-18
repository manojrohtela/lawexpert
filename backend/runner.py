from __future__ import annotations

import json
from pathlib import Path

from .case_processor import process_cases
from .config import PROCESSED_DIR
from .embeddings import HuggingFaceEmbedder
from .law_processor import process_laws
from .vector_store import VectorStore


def _load_json(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _build_points(records: list[dict], embedder: HuggingFaceEmbedder, kind: str) -> list[dict]:
    texts: list[str] = []
    for item in records:
        if kind == "law":
            texts.append(
                f"{item.get('law_name', '')} {item.get('section_or_article', '')} {item.get('text', '')}"
            )
        else:
            texts.append(
                f"{item.get('case_name', '')} {item.get('topic', '')} {item.get('summary', '')} {item.get('key_legal_point', '')}"
            )
    vectors = embedder.embed_texts(texts)
    points: list[dict] = []
    for index, (record, vector) in enumerate(zip(records, vectors), start=1):
        points.append(
            {
                "id": index,
                "vector": vector,
                "payload": record,
            }
        )
    return points


def rebuild_pipeline(
    case_limit: int | None = None,
    build_laws: bool = True,
    build_cases: bool = True,
) -> dict:
    laws_path = PROCESSED_DIR / "laws.json"
    cases_path = PROCESSED_DIR / "cases.json"

    if build_laws:
        laws_path = process_laws()
    if build_cases:
        cases_path = process_cases(limit=case_limit)

    laws = _load_json(laws_path) if laws_path.exists() else []
    cases = _load_json(cases_path) if cases_path.exists() else []

    embedder = HuggingFaceEmbedder()
    store = VectorStore(use_qdrant=True)
    store.ensure_collection("laws_collection", embedder.dimension)
    store.ensure_collection("cases_collection", embedder.dimension)

    if build_laws and laws:
        store.upsert("laws_collection", _build_points(laws, embedder, "law"))
    if build_cases and cases:
        store.upsert("cases_collection", _build_points(cases, embedder, "case"))

    return {
        "laws_path": str(laws_path),
        "cases_path": str(cases_path),
        "laws_count": len(laws),
        "cases_count": len(cases),
    }
