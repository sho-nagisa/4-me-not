from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from fastapi import HTTPException

from backend.app.account_context import get_current_account_id
from backend.db.session import db_session
from backend.models.search.search_log import SearchLog
from backend.services.search.answer import build_rag_answer
from backend.services.search.types import CachedSearchDocument
from backend.services.search.utils import (
    calculate_fuzzy_score,
    calculate_keyword_score,
    calculate_recency_score,
    cosine_similarity,
    ensure_aware_datetime,
    parse_search_date_boundary,
)


logger = logging.getLogger(__name__)


class SearchQueryMixin:
    def search(
        self,
        query: str,
        limit: int = 20,
        target_types: list[str] | None = None,
        date_from: str | datetime | None = None,
        date_to: str | datetime | None = None,
        fuzzy: bool = True,
    ) -> dict:
        normalized_query = query.strip()
        if not normalized_query:
            return self._empty_response(query)

        selected_target_types = self._normalize_target_types(target_types)
        normalized_date_from = parse_search_date_boundary(date_from, "from")
        normalized_date_to = parse_search_date_boundary(date_to, "to")
        if (
            normalized_date_from is not None
            and normalized_date_to is not None
            and normalized_date_from > normalized_date_to
        ):
            raise HTTPException(status_code=400, detail="Search date range is invalid")

        query_embedding, query_embedding_model = self.embedding_provider.embed(
            normalized_query
        )

        account_id = get_current_account_id()
        candidate_limit = (
            10_000
            if normalized_date_from is not None or normalized_date_to is not None
            else max(limit * 50, 300)
        )
        documents = self._load_cached_candidate_documents(
            account_id=account_id,
            target_types=selected_target_types,
            limit=candidate_limit,
        )
        documents = self._filter_documents_by_date(
            documents,
            date_from=normalized_date_from,
            date_to=normalized_date_to,
        )
        results = []

        for document in documents:
            semantic_score = cosine_similarity(
                query_embedding,
                document.embedding,
            )
            keyword_score = calculate_keyword_score(normalized_query, document)
            fuzzy_score = (
                calculate_fuzzy_score(normalized_query, document) if fuzzy else 0.0
            )
            recency_score = calculate_recency_score(document.occurred_at)
            score = (
                0.50 * semantic_score
                + 0.30 * keyword_score
                + 0.10 * fuzzy_score
                + 0.10 * recency_score
            )

            if score <= 0:
                continue

            results.append(
                self._serialize_cached_result(
                    document=document,
                    score=score,
                    semantic_score=semantic_score,
                    keyword_score=keyword_score,
                    fuzzy_score=fuzzy_score,
                    recency_score=recency_score,
                    query=normalized_query,
                )
            )

        results.sort(
            key=lambda item: (
                -item["score"],
                item["occurred_at"] is None,
                item["occurred_at"] or "",
                item["title"],
            )
        )
        limited_results = results[:limit]
        groups = self._group_results(limited_results)
        answer = build_rag_answer(normalized_query, limited_results, groups)
        self._record_search_log(
            account_id=account_id,
            query=normalized_query,
            target_types=selected_target_types,
            results=limited_results,
        )

        return {
            "query": query,
            "embedding_model": query_embedding_model,
            "results": limited_results,
            "groups": groups,
            "answer": answer,
        }

    def _filter_documents_by_date(
        self,
        documents: tuple[CachedSearchDocument, ...],
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> tuple[CachedSearchDocument, ...]:
        if date_from is None and date_to is None:
            return documents

        filtered = []
        for document in documents:
            occurred_at = ensure_aware_datetime(document.occurred_at)
            if occurred_at is None:
                continue
            if date_from is not None and occurred_at < date_from:
                continue
            if date_to is not None and occurred_at > date_to:
                continue
            filtered.append(document)
        return tuple(filtered)

    def _record_search_log(
        self,
        account_id: UUID,
        query: str,
        target_types: list[str] | None,
        results: list[dict],
    ) -> None:
        top_result = results[0] if results else None
        with db_session() as db:
            try:
                db.add(
                    SearchLog(
                        account_id=account_id,
                        query=query,
                        target_types=target_types or [],
                        result_count=len(results),
                        top_result_type=top_result["target_type"] if top_result else None,
                        top_result_id=UUID(top_result["target_id"])
                        if top_result
                        else None,
                    )
                )
                db.commit()
            except Exception:
                db.rollback()
                logger.exception("Failed to record search log")
