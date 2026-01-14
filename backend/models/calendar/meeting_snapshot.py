from __future__ import annotations

from uuid import UUID, uuid4
from datetime import datetime

from sqlmodel import SQLModel, Field


class MeetingSnapshot(SQLModel, table=True):
    __tablename__ = "meeting_snapshots"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    calendar_event_id: UUID = Field(
        foreign_key="calendar_events.id",
        index=True
    )

    # AI生成の直前要約
    summary_text: str

    generated_at: datetime = Field(default_factory=datetime.utcnow)
