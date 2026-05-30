from __future__ import annotations

from threading import RLock
from uuid import UUID

from backend.services.search.cache import SearchDocumentCacheMixin
from backend.services.search.embedding import SearchEmbeddingProvider
from backend.services.search.indexing import SearchIndexingMixin
from backend.services.search.operations import SearchIndexOperationsMixin
from backend.services.search.query import SearchQueryMixin
from backend.services.search.results import SearchResultMixin
from backend.services.search.types import CachedSearchDocument


class SearchService(
    SearchQueryMixin,
    SearchIndexOperationsMixin,
    SearchIndexingMixin,
    SearchDocumentCacheMixin,
    SearchResultMixin,
):
    _cache_lock = RLock()
    _document_cache: dict[UUID, tuple[CachedSearchDocument, ...]] = {}

    def __init__(self, embedding_provider: SearchEmbeddingProvider | None = None) -> None:
        self.embedding_provider = embedding_provider or SearchEmbeddingProvider()

    @classmethod
    def invalidate_cache(cls, account_id: UUID | None = None) -> None:
        with cls._cache_lock:
            if account_id is None:
                cls._document_cache.clear()
            else:
                cls._document_cache.pop(account_id, None)
