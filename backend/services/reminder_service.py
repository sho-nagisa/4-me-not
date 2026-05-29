from datetime import datetime

from fastapi import HTTPException

from backend.app.account_context import get_current_account_id
from backend.db.session import db_session
from backend.models.reminder.reminder import Reminder


class ReminderService:
    def create_reminder(self, title: str, remind_at, message: str | None = None):
        remind_at_value = self._parse_remind_at(remind_at)
        normalized_title = title.strip()
        if not normalized_title:
            raise HTTPException(status_code=400, detail="Reminder title is required")

        with db_session() as db:
            reminder = Reminder(
                account_id=get_current_account_id(),
                title=normalized_title,
                remind_at=remind_at_value,
                message=message.strip() if message else None,
            )
            db.add(reminder)
            db.commit()
            db.refresh(reminder)
            return reminder

    def _parse_remind_at(self, remind_at) -> datetime:
        if isinstance(remind_at, datetime):
            return remind_at
        try:
            return datetime.fromisoformat(str(remind_at).replace("Z", "+00:00"))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Reminder time is invalid") from exc
