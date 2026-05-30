"""add login attempts

Revision ID: d5f6a7b8c9d0
Revises: c4e5f6a7b8c9
Create Date: 2026-05-30 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "c4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "login_attempts",
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="formegot",
    )
    op.create_index(
        "ix_login_attempts_email_created",
        "login_attempts",
        ["email", "created_at"],
        schema="formegot",
    )
    op.create_index(
        "ix_login_attempts_ip_created",
        "login_attempts",
        ["ip_address", "created_at"],
        schema="formegot",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_login_attempts_ip_created",
        table_name="login_attempts",
        schema="formegot",
    )
    op.drop_index(
        "ix_login_attempts_email_created",
        table_name="login_attempts",
        schema="formegot",
    )
    op.drop_table("login_attempts", schema="formegot")
