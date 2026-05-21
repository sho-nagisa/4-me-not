from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base.base import BaseModel
from backend.models.base.enums import TaskStatus


class Task(BaseModel):
    __tablename__ = "tasks"
    __table_args__ = {"schema": "formegot"}

    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("formegot.accounts.id", ondelete="CASCADE"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[TaskStatus] = mapped_column(
        Integer,
        nullable=False,
        default=TaskStatus.TODO,
    )
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    priority: Mapped[int | None] = mapped_column(Integer, nullable=True)

    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="manual_note",
    )
    source_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    is_candidate: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    candidate_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="accepted",
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    links = relationship(
        "TaskLink",
        back_populates="task",
        cascade="all, delete-orphan",
    )
