from uuid import UUID

from sqlalchemy import Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base.base import BaseModel


class TaskLink(BaseModel):
    __tablename__ = "task_links"
    __table_args__ = (
        UniqueConstraint(
            "task_id",
            "target_type",
            "target_id",
            "role",
            name="uq_task_links_target_role",
        ),
        {"schema": "formegot"},
    )

    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("formegot.accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("formegot.tasks.id", ondelete="CASCADE"),
        nullable=False,
    )

    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    task = relationship("Task", back_populates="links")
