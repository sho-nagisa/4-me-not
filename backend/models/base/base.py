from uuid import UUID, uuid4
from datetime import datetime

from sqlmodel import SQLModel, Field


class BaseModel(SQLModel):
    """全テーブル共通の基底クラス"""

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
