from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from .config import settings


@dataclass
class GroqClient:
    api_key: str | None = settings.groq_api_key or None
    model: str = settings.groq_model

    def available(self) -> bool:
        return bool(self.api_key)

    def chat(self, messages: list[dict[str, str]], temperature: float = 0.2) -> str:
        if not self.available():
            return self._offline_response(messages)

        try:
            from groq import Groq  # type: ignore

            client = Groq(api_key=self.api_key)
            completion = client.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore[arg-type]
                temperature=temperature,
            )
            return completion.choices[0].message.content or ""
        except Exception as e:
            print(f"[GroqClient] API error: {e}")
            return self._offline_response(messages)

    def _offline_response(self, messages: list[dict[str, str]]) -> str:
        user_message = ""
        for message in reversed(messages):
            if message.get("role") == "user":
                user_message = message.get("content", "")
                break
        if "summarize" in user_message.lower() or "summary" in user_message.lower():
            return json.dumps(
                {
                    "case_name": "Unknown Case",
                    "year": 0,
                    "court": "Unknown Court",
                    "summary": "The document appears to be a case law judgment but the LLM is unavailable.\nPlease enable GROQ_API_KEY to generate a structured summary.\nThis placeholder preserves the pipeline shape for indexing.\nIt can still be filtered or replaced later.\nThe backend remains functional offline for development.",
                    "key_legal_point": "LLM unavailable, so no legal point extracted.",
                    "relevant_sections": [],
                    "topic": "Unknown",
                }
            )
        return "The legal AI is temporarily unavailable. Please try again shortly."


def extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in LLM response.")
    return json.loads(text[start : end + 1])
