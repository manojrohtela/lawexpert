from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the backend directory, then fall back to the project root
_BACKEND_ENV = Path(__file__).resolve().parent / ".env"
_ROOT_ENV = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_BACKEND_ENV if _BACKEND_ENV.exists() else _ROOT_ENV, override=False)

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
DOCS_DIR = ROOT_DIR / "docs"
DATASET_DIR = ROOT_DIR / "dataset"
PROCESSED_DIR = BACKEND_DIR / "data_processed"


@dataclass(frozen=True)
class Settings:
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key: str = os.getenv("QDRANT_API_KEY", "")
    embedding_model: str = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    auto_build: bool = os.getenv("LEGAL_RAG_AUTO_BUILD", "0") == "1"
    max_case_files: int = int(os.getenv("MAX_CASE_FILES", "0") or 0)
    min_case_chars: int = int(os.getenv("MIN_CASE_CHARS", "2500"))
    max_context_chunks: int = int(os.getenv("MAX_CONTEXT_CHUNKS", "5"))


settings = Settings()

