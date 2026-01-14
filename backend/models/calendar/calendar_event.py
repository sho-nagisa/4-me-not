from __future__ import annotations

from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime

from sqlmodel import SQLModel, Field


class CalendarEvent(SQLModel, table=True):
    __tablename__ = "calendar_events"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Google Calendar 側のID
    external_event_id: str = Field(index=True, unique=True)

    title: str
    start_time: datetime
    end_time: datetime

    # 誰と会う予定か（推定）
    person_id: Optional[UUID] = Field(
        default=None, foreign_key="persons.id"
    )
    community_id: Optional[UUID] = Field(
        default=None, foreign_key="communities.id"
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)
