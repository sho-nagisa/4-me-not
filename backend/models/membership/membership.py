from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime, date

from backend.models.person.person import Person
from sqlmodel import SQLModel, Field, Relationship


class Membership(SQLModel, table=True):
    __tablename__ = "memberships"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # 多重属性の中核
    person_id: UUID = Field(foreign_key="persons.id", index=True)
    community_id: UUID = Field(foreign_key="communities.id", index=True)

    # 文脈上の役割（同期 / 上司 / 共同研究者 など）
    role: Optional[str] = Field(index=True)

    # 主観的重要度（文脈ごと）
    importance: int = Field(default=3, ge=1, le=5)

    # 関係開始・有効期間
    since: Optional[date] = None
    until: Optional[date] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # relationships（循環import回避のため文字列参照）
    person: Optional["Person"] = Relationship()
    community: Optional["Community"] = Relationship()
