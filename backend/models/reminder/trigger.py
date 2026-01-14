from __future__ import annotations

from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime

from sqlmodel import SQLModel, Field


class ReminderTrigger(SQLModel, table=True):
    __tablename__ = "reminder_triggers"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    reminder_id: UUID = Field(
        foreign_key="reminders.id",
        index=True
    )

    trigger_type: str
    # 例:
    # - calendar_event_start
    # - calendar_event_end
    # - fixed_time
    # - relative_time

    # Google Calendar連携用
    calendar_event_id: Optional[str] = None
    offset_minutes: Optional[int] = None   # 開始◯分前/後

    created_at: datetime = Field(default_factory=datetime.utcnow)
