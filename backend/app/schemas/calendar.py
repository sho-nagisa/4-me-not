from datetime import datetime

from pydantic import BaseModel, Field


class EventParticipantRequest(BaseModel):
    person_id: str | None = None
    display_name: str | None = None
    email: str | None = None
    role: str | None = None
    is_inferred: bool = False
    confidence: float | None = None


class CalendarEventCreateRequest(BaseModel):
    title: str
    start_at: datetime
    end_at: datetime
    description: str | None = None
    location: str | None = None
    source: str | None = "manual"
    external_id: str | None = None
    participants: list[EventParticipantRequest] = Field(default_factory=list)
