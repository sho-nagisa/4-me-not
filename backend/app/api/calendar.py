from fastapi import APIRouter, Query

from backend.app.schemas.calendar import CalendarEventCreateRequest
from backend.services.calendar_service import CalendarService


router = APIRouter(prefix="/calendar-events", tags=["calendar"])


@router.get("")
def list_calendar_events(limit: int = Query(default=100, ge=1, le=200)):
    service = CalendarService()
    return service.list_events(limit=limit)


@router.post("")
def create_calendar_event(payload: CalendarEventCreateRequest):
    service = CalendarService()
    return service.create_event(
        title=payload.title,
        start_at=payload.start_at,
        end_at=payload.end_at,
        description=payload.description,
        location=payload.location,
        source=payload.source,
        external_id=payload.external_id,
        participants=[item.model_dump() for item in payload.participants],
    )
