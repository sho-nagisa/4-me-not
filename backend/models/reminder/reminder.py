from __future__ import annotations

from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime, date

from sqlmodel import SQLModel, Field


class Reminder(SQLModel, table=True):
    __tablename__ = "reminders"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # 文脈の核
    person_id: UUID = Field(foreign_key="persons.id", index=True)
    community_id: Optional[UUID] = Field(
        default=None,
        foreign_key="communities.id",
        index=True
    )

    # 何のための通知か
    purpose: str
    # 例:
    # - meeting_preparation
    # - follow_up
    # - log_prompt
    # - birthday
    # - topic_expiry

    message: str                    # 通知本文
    scheduled_for: datetime         # 通知予定時刻

    is_active: bool = Field(default=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)
