"""add search documents

Revision ID: 3d8a9c1f2b7e
Revises: 9ac2d7f1b4e8
Create Date: 2026-05-19 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3d8a9c1f2b7e"
down_revision: Union[str, Sequence[str], None] = "9ac2d7f1b4e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "search_documents",
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("target_id", sa.UUID(), nullable=False),
        sa.Column("person_id", sa.UUID(), nullable=True),
        sa.Column("community_id", sa.UUID(), nullable=True),
        sa.Column("topic_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("search_text", sa.Text(), nullable=False),
        sa.Column("source_text_hash", sa.String(length=64), nullable=False),
        sa.Column("embedding_model", sa.String(length=100), nullable=True),
        sa.Column("embedding_json", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["formegot.accounts.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["community_id"],
            ["formegot.communities.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["person_id"],
            ["formegot.persons.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["topic_id"],
            ["formegot.topics.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "account_id",
            "target_type",
            "target_id",
            name="uq_search_documents_account_target",
        ),
        schema="formegot",
    )
    op.create_index(
        "ix_search_documents_account_target_type",
        "search_documents",
        ["account_id", "target_type"],
        schema="formegot",
    )
    op.create_index(
        "ix_search_documents_person",
        "search_documents",
        ["person_id"],
        schema="formegot",
    )
    op.create_index(
        "ix_search_documents_community",
        "search_documents",
        ["community_id"],
        schema="formegot",
    )
    op.create_index(
        "ix_search_documents_topic",
        "search_documents",
        ["topic_id"],
        schema="formegot",
    )
    op.create_index(
        "ix_search_documents_occurred",
        "search_documents",
        ["occurred_at"],
        schema="formegot",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_search_documents_occurred",
        table_name="search_documents",
        schema="formegot",
    )
    op.drop_index(
        "ix_search_documents_topic",
        table_name="search_documents",
        schema="formegot",
    )
    op.drop_index(
        "ix_search_documents_community",
        table_name="search_documents",
        schema="formegot",
    )
    op.drop_index(
        "ix_search_documents_person",
        table_name="search_documents",
        schema="formegot",
    )
    op.drop_index(
        "ix_search_documents_account_target_type",
        table_name="search_documents",
        schema="formegot",
    )
    op.drop_table("search_documents", schema="formegot")
