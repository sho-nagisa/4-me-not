from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base.base import BaseModel


class AuthSession(BaseModel):
    """Server-side session row for revocable cookie sessions."""

    __tablename__ = "auth_sessions"
    __table_args__ = (
        Index("ix_auth_sessions_account_active", "account_id", "revoked_at"),
        Index("ix_auth_sessions_expires_at", "expires_at"),
        {"schema": "formegot"},
    )

    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("formegot.accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
