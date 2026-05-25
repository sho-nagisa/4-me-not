"""add search logs

Revision ID: b2c7d8e9f104
Revises: 6b7d8e9f0a12
Create Date: 2026-05-25 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "b2c7d8e9f104"
down_revision: Union[str, Sequence[str], None] = "6b7d8e9f0a12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "search_logs",
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column(
            "target_types",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("result_count", sa.Integer(), nullable=False),
        sa.Column("top_result_type", sa.String(length=50), nullable=True),
        sa.Column("top_result_id", sa.UUID(), nullable=True),
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
        "ix_search_logs_account_created",
        "search_logs",
        ["account_id", "created_at"],
        schema="formegot",
    )
    op.create_index(
        "ix_search_logs_account_query_created",
        "search_logs",
        ["account_id", "query", "created_at"],
        schema="formegot",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_search_logs_account_query_created",
        table_name="search_logs",
        schema="formegot",
    )
    op.drop_index(
        "ix_search_logs_account_created",
        table_name="search_logs",
        schema="formegot",
    )
    op.drop_table("search_logs", schema="formegot")
