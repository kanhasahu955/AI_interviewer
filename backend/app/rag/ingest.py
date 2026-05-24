"""Ingest resumes and job descriptions into Pinecone, per-interview namespace."""

from __future__ import annotations

import hashlib
import logging
from typing import Any

from app.rag.chunking import chunk_text
from app.rag.embeddings import embeddings_configured, get_embedding_model
from app.rag.loaders import load_document
from app.rag.pinecone_store import PineconeStore
from app.rag.retriever import interview_namespace

logger = logging.getLogger("app.rag.ingest")


def _vector_id(prefix: str, idx: int, text: str) -> str:
    h = hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}-{idx}-{h}"


def _ingest_chunks(
    text: str,
    *,
    interview_id: int | str,
    kind: str,
    extra_metadata: dict[str, Any] | None = None,
) -> int:
    if not text or not text.strip():
        logger.warning("ingest: empty %s text for interview=%s", kind, interview_id)
        return 0

    if not embeddings_configured():
        raise RuntimeError("OPENAI_API_KEY is required for embeddings")

    store = PineconeStore()
    if not store.enabled:
        raise RuntimeError("PINECONE_API_KEY is not configured")

    chunks = chunk_text(text)
    if not chunks:
        return 0

    embeddings = get_embedding_model()
    vectors_raw = embeddings.embed_documents(chunks)

    payload = []
    for i, (chunk, vec) in enumerate(zip(chunks, vectors_raw)):
        metadata = {
            "interview_id": str(interview_id),
            "kind": kind,
            "chunk_index": i,
            "text": chunk,
        }
        if extra_metadata:
            metadata.update({k: str(v) for k, v in extra_metadata.items()})
        payload.append(
            {
                "id": _vector_id(f"{kind}-{interview_id}", i, chunk),
                "values": vec,
                "metadata": metadata,
            }
        )

    store.upsert_documents(payload, namespace=interview_namespace(interview_id))
    logger.info(
        "ingest: %d %s chunks upserted for interview=%s", len(payload), kind, interview_id
    )
    return len(payload)


def ingest_resume_text(
    text: str, *, interview_id: int | str, candidate_id: int | str | None = None
) -> int:
    return _ingest_chunks(
        text,
        interview_id=interview_id,
        kind="resume",
        extra_metadata={"candidate_id": candidate_id} if candidate_id else None,
    )


def ingest_resume_file(
    file_path: str, *, interview_id: int | str, candidate_id: int | str | None = None
) -> int:
    text = load_document(file_path)
    return ingest_resume_text(
        text, interview_id=interview_id, candidate_id=candidate_id
    )


def ingest_jd_text(
    text: str, *, interview_id: int | str, jd_id: int | str | None = None
) -> int:
    return _ingest_chunks(
        text,
        interview_id=interview_id,
        kind="jd",
        extra_metadata={"jd_id": jd_id} if jd_id else None,
    )


def purge_interview(interview_id: int | str) -> None:
    PineconeStore().delete_namespace(interview_namespace(interview_id))
