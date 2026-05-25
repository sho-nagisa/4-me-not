from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base.base import BaseModel


class SearchLog(BaseModel):
    __tablename__ = "search_logs"
    __table_args__ = {"schema": "formegot"}

    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("formegot.accounts.id", ondelete="CASCADE"),
        nullable=False,
    )

    query: Mapped[str] = mapped_column(Text, nullable=False)
    target_types: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    result_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    top_result_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    top_result_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )
