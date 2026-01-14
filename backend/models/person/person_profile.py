from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship


class PersonProfile(SQLModel, table=True):
    __tablename__ = "person_profiles"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    person_id: UUID = Field(foreign_key="persons.id", unique=True)

    # 記憶・直感系（更新頻度低）
    first_impression: Optional[str] = None
    appearance_feature: Optional[str] = None   # 外見
    vibe_feature: Optional[str] = None         # 雰囲気・直感
    birthday: Optional[str] = None              # 記念日
    distance_feeling: Optional[str] = None      # 距離感（主観）

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # relationship
    person: "Person" = Relationship(back_populates="profile")
