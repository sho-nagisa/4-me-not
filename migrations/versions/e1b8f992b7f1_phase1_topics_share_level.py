"""phase1 topics and share level

Revision ID: e1b8f992b7f1
Revises: 7615aa79d0ae
Create Date: 2026-04-22 01:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e1b8f992b7f1"
down_revision: Union[str, Sequence[str], None] = "7615aa79d0ae"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "topics",
        sa.Column("name", sa.String(length=100), nullable=True, comment="話題名"),
        schema="formegot",
    )
    op.add_column(
        "topics",
        sa.Column("description", sa.Text(), nullable=True, comment="話題の補足"),
        schema="formegot",
    )
    op.add_column(
        "topics",
        sa.Column("parent_id", sa.UUID(), nullable=True, comment="親話題"),
        schema="formegot",
    )
    op.create_foreign_key(
        "fk_topics_parent_id_topics",
        "topics",
        "topics",
        ["parent_id"],
        ["id"],
        source_schema="formegot",
        referent_schema="formegot",
        ondelete="SET NULL",
    )
    op.execute("UPDATE formegot.topics SET name = COALESCE(name, title, 'Untitled')")
    op.alter_column("topics", "name", nullable=False, schema="formegot")

    op.add_column(
        "interactions",
        sa.Column("community_id", sa.UUID(), nullable=True),
        schema="formegot",
    )
    op.add_column(
        "interactions",
        sa.Column("topic_id", sa.UUID(), nullable=True),
        schema="formegot",
    )
    op.add_column(
        "interactions",
        sa.Column(
            "share_level",
            sa.Integer(),
            nullable=False,
            server_default="1",
            comment="どこまで話したか",
        ),
        schema="formegot",
    )
    op.add_column(
        "interactions",
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="実際にやり取りした日時",
        ),
        schema="formegot",
    )
    op.add_column(
        "interactions",
        sa.Column("note", sa.Text(), nullable=True, comment="補足メモ"),
        schema="formegot",
    )
    op.create_foreign_key(
        "fk_interactions_community_id_communities",
        "interactions",
        "communities",
        ["community_id"],
        ["id"],
        source_schema="formegot",
        referent_schema="formegot",
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_interactions_topic_id_topics",
        "interactions",
        "topics",
        ["topic_id"],
        ["id"],
        source_schema="formegot",
        referent_schema="formegot",
        ondelete="SET NULL",
    )
    op.execute("UPDATE formegot.interactions SET occurred_at = created_at WHERE occurred_at IS NULL")
    op.alter_column(
        "interactions",
        "share_level",
        server_default=None,
        schema="formegot",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_interactions_topic_id_topics",
        "interactions",
        schema="formegot",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_interactions_community_id_communities",
        "interactions",
        schema="formegot",
        type_="foreignkey",
    )
    op.drop_column("interactions", "note", schema="formegot")
    op.drop_column("interactions", "occurred_at", schema="formegot")
    op.drop_column("interactions", "share_level", schema="formegot")
    op.drop_column("interactions", "topic_id", schema="formegot")
    op.drop_column("interactions", "community_id", schema="formegot")

    op.drop_constraint(
        "fk_topics_parent_id_topics",
        "topics",
        schema="formegot",
        type_="foreignkey",
    )
    op.drop_column("topics", "parent_id", schema="formegot")
    op.drop_column("topics", "description", schema="formegot")
    op.drop_column("topics", "name", schema="formegot")
