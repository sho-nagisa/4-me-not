from __future__ import annotations

from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlmodel import SQLModel, Field


class ParsedNote(SQLModel, table=True):
    __tablename__ = "parsed_notes"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # 元になった入力
    raw_text: str                           # ユーザーの生メモ
    parsed_json: Dict[str, Any]             # AIが構造化した結果（17項目）

    # 対象（推定）
    person_id: Optional[UUID] = Field(
        default=None, foreign_key="persons.id"
    )
    community_id: Optional[UUID] = Field(
        default=None, foreign_key="communities.id"
    )

    # 状態管理
    is_applied: bool = Field(default=False) # DBに反映済みか
    reviewed_by_user: bool = Field(default=False)

    created_at: datetime = Field(default_factory=datetime.utcnow)
