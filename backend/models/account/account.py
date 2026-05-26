from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base.base import BaseModel


class Account(BaseModel):
    __tablename__ = "accounts"
    __table_args__ = {"schema": "formegot"}

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
