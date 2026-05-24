"""Per-interview RAG retriever over resume + JD chunks."""

from __future__ import annotations

import logging
from typing import Iterable

from app.core.config import settings
from app.rag.embeddings import embeddings_configured, get_embedding_model
from app.rag.pinecone_store import PineconeStore

logger = logging.getLogger("app.rag.retriever")


def interview_namespace(interview_id: int | str) -> str:
    return f"interview-{interview_id}"


class InterviewRetriever:
    def __init__(self):
        self.store = PineconeStore()
        self.embeddings = get_embedding_model() if embeddings_configured() else None

    def _ensure_ready(self) -> None:
        if not self.store.enabled:
            raise RuntimeError("PINECONE_API_KEY is not configured")
        if not embeddings_configured():
            raise RuntimeError("OPENAI_API_KEY is required for embeddings")

    def search(
        self,
        query: str,
        interview_id: int | str,
        kinds: Iterable[str] | None = ("resume", "jd"),
        top_k: int | None = None,
        score_threshold: float | None = None,
    ) -> list[dict]:
        self._ensure_ready()

        top_k = top_k or settings.RAG_TOP_K
        score_threshold = (
            score_threshold
            if score_threshold is not None
            else settings.RAG_SCORE_THRESHOLD
        )

        vector = self.embeddings.embed_query(query)
        metadata_filter = None
        if kinds:
            kinds_list = list(kinds)
            metadata_filter = {"kind": {"$in": kinds_list}}

        result = self.store.query(
            vector,
            top_k=top_k,
            namespace=interview_namespace(interview_id),
            metadata_filter=metadata_filter,
        )

        hits: list[dict] = []
        for match in result.matches:
            score = float(match.score or 0.0)
            if score < score_threshold:
                continue
            hits.append(
                {
                    "id": match.id,
                    "score": score,
                    "metadata": match.metadata or {},
                    "text": (match.metadata or {}).get("text", ""),
                }
            )
        return hits


def format_context(hits: list[dict]) -> str:
    """Render retrieved chunks as a single context block for prompts."""
    if not hits:
        return ""
    lines: list[str] = []
    for i, hit in enumerate(hits, start=1):
        md = hit.get("metadata", {})
        kind = md.get("kind", "doc")
        text = hit.get("text") or md.get("text", "")
        lines.append(f"[{i}] ({kind}, score={hit['score']:.2f})\n{text}")
    return "\n\n".join(lines)
