from fastapi import APIRouter, Query

from backend.services.search import SearchService


router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
def search_memory(
    q: str = Query(..., min_length=1),
    target_type: list[str] | None = Query(default=None),
    date_from: str | None = None,
    date_to: str | None = None,
    fuzzy: bool = True,
    limit: int = Query(default=20, ge=1, le=50),
):
    service = SearchService()
    return service.search(
        query=q,
        target_types=target_type,
        date_from=date_from,
        date_to=date_to,
        fuzzy=fuzzy,
        limit=limit,
    )
