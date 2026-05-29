from datetime import datetime

from pydantic import BaseModel


class InteractionCreateRequest(BaseModel):
    occurred_at: datetime | None = None
    person_id: str
    community_id: str | None = None
    topic_id: str | None = None
    interaction_type: str
    share_level: str = "SHARED"
    content: str
    note: str | None = None


class InteractionRecordedResponse(BaseModel):
    status: str
    interaction_id: str
