from __future__ import annotations

import json
import math
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import PROCESSED_DIR, settings


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


@dataclass
class QdrantHttpClient:
    base_url: str = settings.qdrant_url.rstrip("/")
    api_key: str | None = settings.qdrant_api_key or None

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        url = f"{self.base_url}{path}"
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["api-key"] = self.api_key
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as response:
            content = response.read().decode("utf-8")
            return json.loads(content) if content else {}

    def collection_exists(self, name: str) -> bool:
        try:
            self._request("GET", f"/collections/{name}")
            return True
        except Exception:
            return False

    def create_collection(self, name: str, vector_size: int) -> None:
        payload = {
            "vectors": {
                "size": vector_size,
                "distance": "Cosine",
            }
        }
        try:
            self._request("PUT", f"/collections/{name}", payload)
        except Exception:
            pass

    def upsert(self, collection: str, points: list[dict[str, Any]]) -> None:
        if not points:
            return
        # Qdrant accepts max 100 points per batch
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            payload = {"points": batch}
            try:
                self._request("PUT", f"/collections/{collection}/points?wait=true", payload)
            except Exception as e:
                print(f"[Qdrant] upsert error on {collection} batch {i//batch_size}: {e}")

    def search(self, collection: str, vector: list[float], limit: int = 5) -> list[dict]:
        payload = {
            "vector": vector,
            "limit": limit,
            "with_payload": True,
            "with_vector": False,
        }
        try:
            response = self._request("POST", f"/collections/{collection}/points/search", payload)
            return response.get("result", [])
        except Exception:
            return []


@dataclass
class LocalVectorStore:
    store_path: Path = PROCESSED_DIR / "local_vectors.json"

    def __post_init__(self) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self._data = {"laws_collection": [], "cases_collection": []}
        if self.store_path.exists():
            try:
                self._data = json.loads(self.store_path.read_text(encoding="utf-8"))
            except Exception:
                pass

    def save(self) -> None:
        self.store_path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")

    def upsert(self, collection: str, points: list[dict[str, Any]]) -> None:
        self._data.setdefault(collection, [])
        existing = {item["id"]: item for item in self._data[collection]}
        for point in points:
            existing[str(point["id"])] = point
        self._data[collection] = list(existing.values())
        self.save()

    def search(self, collection: str, vector: list[float], limit: int = 5) -> list[dict]:
        results: list[dict] = []
        for point in self._data.get(collection, []):
            score = cosine_similarity(vector, point.get("vector", []))
            results.append({"id": point["id"], "score": score, "payload": point.get("payload", {})})
        results.sort(key=lambda item: item["score"], reverse=True)
        return results[:limit]


class VectorStore:
    def __init__(self, use_qdrant: bool = True):
        self.qdrant = QdrantHttpClient()
        self.local = LocalVectorStore()
        self.use_qdrant = use_qdrant

    def ensure_collection(self, name: str, vector_size: int) -> None:
        if self.use_qdrant and self.qdrant:
            try:
                self.qdrant.create_collection(name, vector_size)
                return
            except Exception:
                pass

    def upsert(self, collection: str, points: list[dict[str, Any]]) -> None:
        if self.use_qdrant:
            self.qdrant.upsert(collection, points)
        self.local.upsert(collection, points)

    def search(self, collection: str, vector: list[float], limit: int = 5) -> list[dict]:
        results = self.qdrant.search(collection, vector, limit=limit) if self.use_qdrant else []
        if results:
            return [
                {
                    "id": item.get("id"),
                    "score": item.get("score", 0.0),
                    "payload": item.get("payload", {}),
                }
                for item in results
            ]
        return self.local.search(collection, vector, limit=limit)

