from __future__ import annotations

from datetime import datetime, time, timezone
from difflib import SequenceMatcher
import json
import math
import re
import unicodedata
from uuid import UUID

from fastapi import HTTPException

from backend.models.base.enums import TaskStatus


def normalize_uuid(value: str, detail: str) -> UUID:
    try:
        return UUID(str(value))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=detail) from exc


def task_status_label(status: TaskStatus | int) -> str:
    normalized = TaskStatus(status)
    labels = {
        TaskStatus.TODO: "未完了",
        TaskStatus.DONE: "完了",
        TaskStatus.SKIPPED: "スキップ",
    }
    return labels.get(normalized, normalized.name)


def normalize_text(value: str | None) -> str:
    return unicodedata.normalize("NFKC", value or "").casefold()


def normalize_vector(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def parse_embedding(value: str | None) -> list[float]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [float(item) for item in parsed if isinstance(item, int | float)]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    score = sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)
    return max(0.0, min(1.0, score))


def calculate_keyword_score(query: str, document: SearchDocument) -> float:
    normalized_query = normalize_text(query)
    if not normalized_query:
        return 0.0

    title = normalize_text(document.title)
    summary = normalize_text(document.summary)
    body = normalize_text(document.search_text)
    combined = "\n".join([title, summary, body])
    terms = build_query_terms(normalized_query)
    if not terms:
        return 0.0

    matched_terms = sum(1 for term in terms if term in combined)
    coverage = matched_terms / len(terms)
    exact_boost = 0.35 if normalized_query in combined else 0.0
    title_boost = 0.20 if normalized_query in title else 0.0
    if not title_boost and any(term in title for term in terms):
        title_boost = 0.10

    return min(1.0, exact_boost + title_boost + 0.55 * coverage)


def calculate_fuzzy_score(query: str, document: SearchDocument) -> float:
    normalized_query = normalize_text(query)
    if not normalized_query:
        return 0.0

    title = normalize_text(document.title)
    summary = normalize_text(document.summary)
    body = normalize_text(document.search_text)
    combined = compact_text("\n".join([title, summary, body]), 3000) or ""
    compact_query = re.sub(r"\s+", "", normalized_query)
    compact_combined = re.sub(r"\s+", "", combined)

    if not compact_query or not compact_combined:
        return 0.0
    if compact_query in compact_combined:
        return 1.0

    token_score = _best_token_similarity(normalized_query, combined)
    ngram_score = _ngram_overlap_score(compact_query, compact_combined)
    title_score = _ngram_overlap_score(compact_query, re.sub(r"\s+", "", title))
    return min(1.0, max(token_score, ngram_score * 0.9, title_score))


def build_query_terms(query: str) -> set[str]:
    terms = {token for token in re.findall(r"[\w]+", query) if len(token) > 1}
    compact = re.sub(r"\s+", "", query)
    for width in (2, 3):
        if len(compact) < width:
            continue
        for index in range(len(compact) - width + 1):
            terms.add(compact[index : index + width])
            if len(terms) >= 80:
                return terms
    return terms


def parse_search_date_boundary(value: str | datetime | None, mode: str) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value).strip()
        if not text:
            return None
        try:
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
                boundary_time = time.min if mode == "from" else time.max
                parsed = datetime.combine(datetime.fromisoformat(text).date(), boundary_time)
            else:
                parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Search date is invalid") from exc
    return ensure_aware_datetime(parsed)


def ensure_aware_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def calculate_recency_score(occurred_at: datetime | None) -> float:
    if occurred_at is None:
        return 0.0
    occurred_at = ensure_aware_datetime(occurred_at)
    days = max(0, (datetime.now(timezone.utc) - occurred_at).days)
    return 1 / (1 + days / 180)


def extract_snippet(query: str, document: SearchDocument, length: int = 180) -> str:
    source = document.summary or document.search_text
    compact_source = compact_text(source, 1000)
    folded_source = normalize_text(compact_source)
    folded_query = normalize_text(query)
    index = folded_source.find(folded_query) if folded_query else -1
    if index < 0:
        return compact_text(compact_source, length)

    start = max(0, index - 50)
    end = min(len(compact_source), index + len(query) + 100)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(compact_source) else ""
    return f"{prefix}{compact_source[start:end]}{suffix}"


def compact_text(value: str | None, max_length: int = 200) -> str | None:
    if not value:
        return None
    compacted = re.sub(r"\s+", " ", value).strip()
    if len(compacted) <= max_length:
        return compacted
    return compacted[: max_length - 1].rstrip() + "..."


def first_non_empty(*values: str | None) -> str | None:
    for value in values:
        if value and value.strip():
            return value.strip()
    return None


def join_search_parts(parts: list[str | None]) -> str:
    return "\n".join(part.strip() for part in parts if part and part.strip())


def _best_token_similarity(query: str, combined: str) -> float:
    query_tokens = [token for token in re.findall(r"[\w]+", query) if len(token) > 2]
    document_tokens = [
        token for token in re.findall(r"[\w]+", combined) if len(token) > 2
    ]
    if not query_tokens or not document_tokens:
        return 0.0

    best_scores = []
    for query_token in query_tokens[:12]:
        candidates = [
            token
            for token in document_tokens
            if abs(len(token) - len(query_token)) <= max(2, len(query_token) // 3)
        ]
        best = max(
            (
                SequenceMatcher(None, query_token, token).ratio()
                for token in candidates[:400]
            ),
            default=0.0,
        )
        best_scores.append(best)

    if not best_scores:
        return 0.0
    return sum(best_scores) / len(best_scores)


def _ngram_overlap_score(query: str, combined: str) -> float:
    query_grams = _character_grams(query)
    if not query_grams:
        return 0.0
    combined_grams = _character_grams(combined)
    if not combined_grams:
        return 0.0
    return len(query_grams & combined_grams) / len(query_grams)


def _character_grams(value: str) -> set[str]:
    grams: set[str] = set()
    compact = re.sub(r"\s+", "", value)
    for width in (2, 3):
        if len(compact) < width:
            continue
        for index in range(len(compact) - width + 1):
            grams.add(compact[index : index + width])
            if len(grams) >= 200:
                return grams
    return grams


