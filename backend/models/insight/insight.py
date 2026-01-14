from __future__ import annotations

from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime

from sqlmodel import SQLModel, Field


class Insight(SQLModel, table=True):
    __tablename__ = "insights"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # 誰についての洞察か
    person_id: UUID = Field(foreign_key="persons.id", index=True)

    # 種別（固定語彙にしてもOK）
    type: str = Field(index=True)
    # 例:
    # - like        （好きなもの）
    # - dislike     （苦手なもの）
    # - vibe        （雰囲気・直感）
    # - strength    （強み）
    # - caution     （注意点）
    # - gift        （贈り物・支援履歴）

    value: str                      # 内容（自由記述）
    confidence: Optional[int] = Field(
        default=None, ge=1, le=5
    )                                # 主観的確度（任意）

    # 情報の由来
    source: str = Field(default="human")  
    # human / ai / mixed

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
