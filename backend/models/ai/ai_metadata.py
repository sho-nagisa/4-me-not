from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime

from sqlmodel import SQLModel, Field


class AIMetadata(SQLModel, table=True):
    __tablename__ = "ai_metadata"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    parsed_note_id: UUID = Field(
        foreign_key="parsed_notes.id",
        index=True
    )

    model_name: str            # gemini-1.5-pro など
    confidence_score: Optional[int] = Field(
        default=None, ge=1, le=5
    )

    inferred_fields: Optional[str] = None
    # 例: "community, next_topic, like"

    warnings: Optional[str] = None
    # 例: "community_ambiguous"

    created_at: datetime = Field(default_factory=datetime.utcnow)
