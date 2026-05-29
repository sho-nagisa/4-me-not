from fastapi import APIRouter

from backend.app.schemas.common import IdResponse
from backend.app.schemas.reminder import ReminderCreateRequest
from backend.services.reminder_service import ReminderService


router = APIRouter(prefix="/reminders", tags=["reminder"])


@router.post("", response_model=IdResponse)
def create_reminder(payload: ReminderCreateRequest) -> IdResponse:
    service = ReminderService()
    reminder = service.create_reminder(
        title=payload.title,
        remind_at=payload.remind_at,
        message=payload.message,
    )
    return IdResponse(id=str(reminder.id))
