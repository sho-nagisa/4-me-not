"""add overview performance indexes

Revision ID: 2c5f9e7b1a0d
Revises: 7f6a4e2b1c55
Create Date: 2026-05-13 20:10:00.000000
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "2c5f9e7b1a0d"
down_revision: Union[str, Sequence[str], None] = "7f6a4e2b1c55"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_interactions_occurred_created",
        "interactions",
        ["occurred_at", "created_at"],
        schema="formegot",
    )
    op.create_index(
        "ix_interactions_person_occurred_created",
        "interactions",
        ["person_id", "occurred_at", "created_at"],
        schema="formegot",
    )
    op.create_index(
        "ix_interactions_community_occurred_created",
        "interactions",
        ["community_id", "occurred_at", "created_at"],
        schema="formegot",
    )
    op.create_index(
        "ix_interactions_topic_occurred_created",
        "interactions",
        ["topic_id", "occurred_at", "created_at"],
        schema="formegot",
    )
    op.create_index(
        "ix_interactions_share_occurred_created",
        "interactions",
        ["share_level", "occurred_at", "created_at"],
        schema="formegot",
    )
    op.create_index(
        "ix_persons_visible_name",
        "persons",
        ["is_hidden", "name"],
        schema="formegot",
    )
    op.create_index(
        "ix_persons_primary_community",
        "persons",
        ["primary_community_id"],
        schema="formegot",
    )
    op.create_index(
        "ix_communities_visible_name",
        "communities",
        ["is_hidden", "name"],
        schema="formegot",
    )
    op.create_index(
        "ix_communities_parent",
        "communities",
        ["parent_id"],
        schema="formegot",
    )
    op.create_index(
        "ix_topics_parent_name",
        "topics",
        ["parent_id", "name"],
        schema="formegot",
    )
    op.create_index(
        "ix_topics_name",
        "topics",
        ["name"],
        schema="formegot",
    )


def downgrade() -> None:
    op.drop_index("ix_topics_name", table_name="topics", schema="formegot")
    op.drop_index("ix_topics_parent_name", table_name="topics", schema="formegot")
    op.drop_index("ix_communities_parent", table_name="communities", schema="formegot")
    op.drop_index("ix_communities_visible_name", table_name="communities", schema="formegot")
    op.drop_index("ix_persons_primary_community", table_name="persons", schema="formegot")
    op.drop_index("ix_persons_visible_name", table_name="persons", schema="formegot")
    op.drop_index(
        "ix_interactions_share_occurred_created",
        table_name="interactions",
        schema="formegot",
    )
    op.drop_index(
        "ix_interactions_topic_occurred_created",
        table_name="interactions",
        schema="formegot",
    )
    op.drop_index(
        "ix_interactions_community_occurred_created",
        table_name="interactions",
        schema="formegot",
    )
    op.drop_index(
        "ix_interactions_person_occurred_created",
        table_name="interactions",
        schema="formegot",
    )
    op.drop_index(
        "ix_interactions_occurred_created",
        table_name="interactions",
        schema="formegot",
    )
