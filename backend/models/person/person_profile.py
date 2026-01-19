from sqlalchemy import String, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base.base import BaseModel


class PersonProfile(BaseModel):
    """
    PersonProfile（第一印象・直感・特徴）
    - 時間経過で変化しうる主観的情報
    - 1 Person : 0..1 Profile を想定
    """

    __tablename__ = "person_profiles"

    person_id: Mapped[str] = mapped_column(
        ForeignKey("persons.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="対応する Person"
    )

    first_impression: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="第一印象（短文）"
    )

    intuition: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="直感・感覚的なメモ"
    )

    vibe_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="雰囲気スコア（例: -5〜+5）"
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="その他の特徴・補足"
    )

    person = relationship(
        "Person",
        backref="profile",
        lazy="joined"
    )
