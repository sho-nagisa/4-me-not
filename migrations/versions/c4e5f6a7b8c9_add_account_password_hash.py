"""add account password hash

Revision ID: c4e5f6a7b8c9
Revises: b2c7d8e9f104
Create Date: 2026-05-26 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "b2c7d8e9f104"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "accounts",
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        schema="formegot",
    )


def downgrade() -> None:
    op.drop_column("accounts", "password_hash", schema="formegot")
