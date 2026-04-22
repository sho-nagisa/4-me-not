"""person primary community

Revision ID: a84f0d5c91e2
Revises: e1b8f992b7f1
Create Date: 2026-04-22 14:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a84f0d5c91e2"
down_revision: Union[str, Sequence[str], None] = "e1b8f992b7f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "persons",
        sa.Column(
            "primary_community_id",
            sa.UUID(),
            nullable=True,
            comment="主な所属コミュニティ",
        ),
        schema="formegot",
    )
    op.create_foreign_key(
        "fk_persons_primary_community_id_communities",
        "persons",
        "communities",
        ["primary_community_id"],
        ["id"],
        source_schema="formegot",
        referent_schema="formegot",
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_persons_primary_community_id_communities",
        "persons",
        schema="formegot",
        type_="foreignkey",
    )
    op.drop_column("persons", "primary_community_id", schema="formegot")
