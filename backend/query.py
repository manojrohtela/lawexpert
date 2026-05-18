from __future__ import annotations

import re
from dataclasses import dataclass

from .models import QueryIntent


SECTION_HINTS = {
    "section",
    "article",
    "ipc",
    "bns",
    "bnss",
    "bsa",
    "constitution",
    "act",
    "penal",
}

CASE_HINTS = {
    "case",
    "judgment",
    "judgement",
    "precedent",
    "bail",
    "appeal",
    "petition",
    "supreme court",
    "high court",
    "ratio",
}


def understand_query(query: str) -> QueryIntent:
    text = query.lower()
    needs_section = any(hint in text for hint in SECTION_HINTS)
    needs_case = any(hint in text for hint in CASE_HINTS)

    if re.search(r"\bsection\s+\d+", text) or re.search(r"\barticle\s+\d+", text):
        needs_section = True
    if re.search(r"\bvs\b|\bversus\b", text):
        needs_case = True

    if not needs_section and not needs_case:
        needs_section = True
        needs_case = True

    return QueryIntent(needs_section=needs_section, needs_case=needs_case)

