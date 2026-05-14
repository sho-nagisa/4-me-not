from datetime import datetime

from backend.app.account_context import get_current_account_id
from backend.db.session import SessionLocal
from backend.models.reminder.reminder import Reminder


class ReminderService:
    def create_reminder(self, title: str, remind_at, message: str | None = None):
        remind_at_value = self._parse_remind_at(remind_at)

        db = SessionLocal()
        try:
            reminder = Reminder(
                account_id=get_current_account_id(),
                title=title,
                remind_at=remind_at_value,
                message=message,
            )
            db.add(reminder)
            db.commit()
            db.refresh(reminder)
            return reminder
        finally:
            db.close()

    def _parse_remind_at(self, remind_at) -> datetime:
        if isinstance(remind_at, datetime):
            return remind_at
        return datetime.fromisoformat(str(remind_at).replace("Z", "+00:00"))
