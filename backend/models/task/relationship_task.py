from sqlalchemy import String, Text, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base.base import BaseModel
from backend.models.base.enums import TaskStatus


class RelationshipTask(BaseModel):
    """
    人間関係タスク（文脈依存）
    - フォローアップ・確認・行動メモ
    """

    __tablename__ = "relationship_tasks"
    __table_args__ = {"schema": "formegot"}

    person_id: Mapped[str] = mapped_column(
        ForeignKey("formegot.persons.id", ondelete="CASCADE"),
        nullable=False
    )

    title: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    status: Mapped[TaskStatus] = mapped_column(
        Integer,
        nullable=False,
        default=TaskStatus.TODO
    )

    person = relationship("Person", backref="relationship_tasks")
