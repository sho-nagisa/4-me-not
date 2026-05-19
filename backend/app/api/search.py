from fastapi import APIRouter, Query

from backend.services.search_service import SearchService


router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
def search_memory(
    q: str = Query(..., min_length=1),
    target_type: list[str] | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
):
    service = SearchService()
    return service.search(
        query=q,
        target_types=target_type,
        limit=limit,
    )
