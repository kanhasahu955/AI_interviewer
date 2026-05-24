"""Pinecone vector index wrapper."""

from __future__ import annotations

import logging

from app.core.config import settings

logger = logging.getLogger("app.rag.pinecone")


class PineconeStore:
    EMBEDDING_DIMENSION = 1536  # text-embedding-3-small

    def __init__(self):
        self._index = None
        self._client = None
        self._enabled = bool(settings.PINECONE_API_KEY)

    @property
    def enabled(self) -> bool:
        return self._enabled

    def _get_client(self):
        if self._client is None:
            from pinecone import Pinecone

            self._client = Pinecone(api_key=settings.PINECONE_API_KEY)
        return self._client

    def _ensure_index(self):
        from pinecone import ServerlessSpec

        pc = self._get_client()
        name = settings.PINECONE_INDEX_NAME

        if not pc.has_index(name):
            region = settings.PINECONE_ENV or "us-east-1"
            pc.create_index(
                name=name,
                dimension=self.EMBEDDING_DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=region),
            )

    def _get_index(self):
        if not self._enabled:
            raise RuntimeError("PINECONE_API_KEY is not configured")

        if self._index is None:
            self._ensure_index()
            self._index = self._get_client().Index(settings.PINECONE_INDEX_NAME)

        return self._index

    def upsert_documents(
        self, vectors: list[dict], namespace: str | None = None
    ) -> None:
        if not vectors:
            return

        ns = namespace or settings.PINECONE_NAMESPACE
        index = self._get_index()
        index.upsert(vectors=vectors, namespace=ns)

    def query(
        self,
        vector: list[float],
        top_k: int = 5,
        namespace: str | None = None,
        metadata_filter: dict | None = None,
    ):
        ns = namespace or settings.PINECONE_NAMESPACE
        index = self._get_index()
        kwargs = dict(
            vector=vector,
            top_k=top_k,
            include_metadata=True,
            namespace=ns,
        )
        if metadata_filter:
            kwargs["filter"] = metadata_filter
        return index.query(**kwargs)

    def delete_namespace(self, namespace: str) -> None:
        try:
            index = self._get_index()
            index.delete(delete_all=True, namespace=namespace)
        except Exception as exc:
            logger.warning("Pinecone delete_namespace(%s) failed: %s", namespace, exc)
