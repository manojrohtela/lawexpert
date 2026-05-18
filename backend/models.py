from __future__ import annotations

from typing import List, Literal, Optional

try:
    from pydantic import BaseModel, Field
except Exception:  # pragma: no cover - lightweight fallback for minimal environments
    class BaseModel:  # type: ignore[override]
        def __init__(self, **data):
            for key, value in data.items():
                setattr(self, key, value)

        def model_dump(self):
            return dict(self.__dict__)

    def Field(default=None, default_factory=None, **kwargs):  # type: ignore[override]
        if default_factory is not None:
            return default_factory()
        return default


class LawRecord(BaseModel):
    text: str
    law_name: str
    section_or_article: str
    type: Literal["law"] = "law"


class CaseRecord(BaseModel):
    case_name: str
    year: int
    court: str = ""
    summary: str
    key_legal_point: str
    relevant_sections: List[str] = Field(default_factory=list)
    topic: str
    type: Literal["case"] = "case"
    source_file: Optional[str] = None


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class QueryRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=10)
    history: List[ChatMessage] = Field(default_factory=list)


class QueryIntent(BaseModel):
    needs_section: bool
    needs_case: bool


class SearchHit(BaseModel):
    score: float
    payload: dict


class ChatResponse(BaseModel):
    intent: QueryIntent
    answer: str
    law_hits: List[SearchHit]
    case_hits: List[SearchHit]
