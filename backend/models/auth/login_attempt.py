from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base.base import BaseModel


class LoginAttempt(BaseModel):
    """Failed login attempt, used for DB-backed login rate limiting."""

    __tablename__ = "login_attempts"
    __table_args__ = (
        Index("ix_login_attempts_email_created", "email", "created_at"),
        Index("ix_login_attempts_ip_created", "ip_address", "created_at"),
        {"schema": "formegot"},
    )

    email: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
