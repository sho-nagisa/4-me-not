from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.reminder_service import ReminderService


router = APIRouter(prefix="/reminders", tags=["reminder"])


class ReminderCreateRequest(BaseModel):
    title: str
    remind_at: str
    message: str | None = None


@router.post("")
def create_reminder(payload: ReminderCreateRequest):
    service = ReminderService()
    reminder = service.create_reminder(
        title=payload.title,
        remind_at=payload.remind_at,
        message=payload.message,
    )
    return {"id": str(reminder.id)}
