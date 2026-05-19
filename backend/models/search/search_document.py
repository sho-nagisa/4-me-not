from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base.base import BaseModel


class SearchDocument(BaseModel):
    __tablename__ = "search_documents"
    __table_args__ = (
        UniqueConstraint(
            "account_id",
            "target_type",
            "target_id",
            name="uq_search_documents_account_target",
        ),
        {"schema": "formegot"},
    )

    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("formegot.accounts.id", ondelete="CASCADE"),
        nullable=False,
    )

    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)

    person_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("formegot.persons.id", ondelete="CASCADE"),
        nullable=True,
    )
    community_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("formegot.communities.id", ondelete="SET NULL"),
        nullable=True,
    )
    topic_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("formegot.topics.id", ondelete="SET NULL"),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    search_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_text_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    embedding_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    embedding_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    indexed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    person = relationship("Person")
    community = relationship("Community")
    topic = relationship("Topic")
