"""add auth sessions

Revision ID: e6f7a8b9c0d1
Revises: d5f6a7b8c9d0
Create Date: 2026-06-06 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e6f7a8b9c0d1"
down_revision: Union[str, Sequence[str], None] = "d5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "auth_sessions",
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["formegot.accounts.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="formegot",
    )
    op.create_index(
        "ix_auth_sessions_account_active",
        "auth_sessions",
        ["account_id", "revoked_at"],
        schema="formegot",
    )
    op.create_index(
        "ix_auth_sessions_expires_at",
        "auth_sessions",
        ["expires_at"],
        schema="formegot",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_auth_sessions_expires_at",
        table_name="auth_sessions",
        schema="formegot",
    )
    op.drop_index(
        "ix_auth_sessions_account_active",
        table_name="auth_sessions",
        schema="formegot",
    )
    op.drop_table("auth_sessions", schema="formegot")
