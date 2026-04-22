"""add hidden flags to people and communities

Revision ID: 7f6a4e2b1c55
Revises: a84f0d5c91e2
Create Date: 2026-04-22 20:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7f6a4e2b1c55"
down_revision = "a84f0d5c91e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "persons",
        sa.Column(
            "is_hidden",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        schema="formegot",
    )
    op.add_column(
        "communities",
        sa.Column(
            "is_hidden",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        schema="formegot",
    )


def downgrade() -> None:
    op.drop_column("communities", "is_hidden", schema="formegot")
    op.drop_column("persons", "is_hidden", schema="formegot")
