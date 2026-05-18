from __future__ import annotations

import json
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import PROCESSED_DIR, settings
from .embeddings import HuggingFaceEmbedder
from .llm_client import GroqClient
from .models import ChatResponse, ChatMessage, QueryIntent, QueryRequest, SearchHit
from .query import understand_query
from .runner import rebuild_pipeline
from .stats import build_stats, build_suggestions
from .vector_store import VectorStore


SYSTEM_PROMPT = """You are LexAI, a brilliant senior Indian legal expert and advocate with 30+ years of experience.
You have mastered the BNS (Bharatiya Nyaya Sanhita), BNSS, BSA, IPC, Constitution of India, IT Act, NDPS Act, Motor Vehicles Act, and all major Indian laws.

Your personality:
- Warm, confident, and conversational — like a knowledgeable friend who happens to be a lawyer
- You speak clearly, never use unnecessary jargon without explaining it
- You are thorough but concise — you give the actual answer, not just "consult a lawyer"
- You cite specific sections and real cases when you know them

Your approach (HYBRID):
1. PRIMARY: Use the retrieved legal context (RAG data) as your main source — these are real extracted sections and case summaries
2. SECONDARY: Supplement with your own deep legal knowledge when the context doesn't fully cover the question
3. Always be clear when citing a retrieved section vs your general knowledge
4. For serious matters (criminal charges, contracts, custody), recommend professional legal counsel at the end

Response format:
- Start with a direct answer to the question
- Cite the relevant law section(s) in **bold**
- If a case example is available, mention it naturally
- End with a practical explanation in plain language
- Use markdown formatting (bold, bullet points) for clarity"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.auto_build:
        rebuild_pipeline(case_limit=settings.max_case_files or None)
    yield


app = FastAPI(title="Legal AI RAG Backend", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _load_json(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


@lru_cache(maxsize=1)
def get_embedder() -> HuggingFaceEmbedder:
    return HuggingFaceEmbedder()


@lru_cache(maxsize=1)
def get_store() -> VectorStore:
    return VectorStore(use_qdrant=True)


@lru_cache(maxsize=1)
def get_llm() -> GroqClient:
    return GroqClient()


def _load_context_results(collection: str, query: str, limit: int) -> list[SearchHit]:
    embedder = get_embedder()
    store = get_store()
    vector = embedder.embed_query(query)
    results = store.search(collection, vector, limit=limit)
    return [SearchHit(score=item.get("score", 0.0), payload=item.get("payload", {})) for item in results]


def _build_context_block(law_hits: list[SearchHit], case_hits: list[SearchHit]) -> str:
    lines: list[str] = []
    for idx, hit in enumerate(law_hits, start=1):
        p = hit.payload
        text = (p.get("text") or "")[:900]
        lines.append(f"[RETRIEVED LAW {idx}]\nAct: {p.get('law_name')} | {p.get('section_or_article')}\n{text}")
    for idx, hit in enumerate(case_hits, start=1):
        p = hit.payload
        lines.append(
            f"[RETRIEVED CASE {idx}]\nCase: {p.get('case_name')} ({p.get('year')}) — {p.get('court')}\n"
            f"Topic: {p.get('topic')}\n"
            f"Summary: {(p.get('summary') or '')[:400]}\n"
            f"Key legal point: {p.get('key_legal_point')}"
        )
    return "\n\n".join(lines)


def _build_answer(
    query: str,
    intent: QueryIntent,
    law_hits: list[SearchHit],
    case_hits: list[SearchHit],
    history: list[ChatMessage],
) -> str:
    llm = get_llm()

    # Offline fallback
    if not llm.available():
        parts: list[str] = []
        if law_hits:
            law = law_hits[0].payload
            parts.append(f"**{law.get('law_name')} — {law.get('section_or_article')}**")
            parts.append((law.get("text") or "")[:700])
        if case_hits:
            case = case_hits[0].payload
            parts.append(f"\n**Case:** {case.get('case_name')} ({case.get('year')}) — {case.get('court')}")
            parts.append((case.get("summary") or "")[:500])
        if not parts:
            parts.append("I couldn't find relevant legal context for your query.")
        return "\n\n".join(parts)

    # Build messages — system + history + current turn with RAG context injected
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add prior conversation (last 6 turns to stay within token limits)
    for msg in history[-6:]:
        messages.append({"role": msg.role, "content": msg.content})

    # Inject RAG context into the current user message
    context_block = _build_context_block(law_hits, case_hits)
    if context_block:
        user_content = (
            f"{query}\n\n"
            f"--- Retrieved Legal Context (use as primary reference) ---\n"
            f"{context_block}"
        )
    else:
        user_content = query

    messages.append({"role": "user", "content": user_content})

    return llm.chat(messages, temperature=0.4)


@app.get("/health")
def health() -> dict:
    laws = _load_json(PROCESSED_DIR / "laws.json")
    cases = _load_json(PROCESSED_DIR / "cases.json")
    return {
        "status": "ok",
        "laws_loaded": len(laws),
        "cases_loaded": len(cases),
        "groq_configured": bool(settings.groq_api_key),
        "qdrant_url": settings.qdrant_url,
    }


@app.get("/stats")
def stats() -> dict:
    return build_stats()


@app.get("/suggestions")
def suggestions() -> dict:
    return {"suggestions": build_suggestions()}


@app.post("/chat", response_model=ChatResponse)
def chat(request: QueryRequest) -> ChatResponse:
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    intent = understand_query(request.query)
    law_hits: list[SearchHit] = []
    case_hits: list[SearchHit] = []

    # Always search both when ambiguous; otherwise follow intent
    if intent.needs_section:
        law_hits = _load_context_results("laws_collection", request.query, request.top_k)
    if intent.needs_case:
        case_hits = _load_context_results("cases_collection", request.query, request.top_k)

    # Even if no RAG hits, still let the LLM answer from its own knowledge
    answer = _build_answer(request.query, intent, law_hits, case_hits, request.history)
    return ChatResponse(intent=intent, answer=answer, law_hits=law_hits, case_hits=case_hits)


@app.post("/rebuild")
def rebuild(
    case_limit: int | None = None,
    skip_laws: bool = False,
    skip_cases: bool = False,
) -> dict:
    return rebuild_pipeline(
        case_limit=case_limit,
        build_laws=not skip_laws,
        build_cases=not skip_cases,
    )
