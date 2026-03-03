from fastapi import APIRouter
from backend.services.reminder_service import ReminderService

router = APIRouter(prefix="/reminders", tags=["reminder"])


@router.post("/")
def create_reminder(title: str, remind_at: str, message: str | None = None):
    service = ReminderService()
    reminder = service.create_reminder(title, remind_at, message)
    return {"id": reminder.id}
