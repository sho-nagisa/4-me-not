"""add account scope foundation

Revision ID: 9ac2d7f1b4e8
Revises: 2c5f9e7b1a0d
Create Date: 2026-05-14 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9ac2d7f1b4e8"
down_revision: Union[str, Sequence[str], None] = "2c5f9e7b1a0d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DEFAULT_ACCOUNT_ID = "00000000-0000-0000-0000-000000000001"
DEFAULT_ACCOUNT_EMAIL = "debug@example.local"
SCOPED_TABLES = ("persons", "communities", "topics", "interactions", "reminders")


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        schema="formegot",
    )
    op.create_index(
        "ix_accounts_email",
        "accounts",
        ["email"],
        unique=True,
        schema="formegot",
    )
    op.execute(
        f"""
        INSERT INTO formegot.accounts (id, email, is_active, created_at, updated_at)
        VALUES ('{DEFAULT_ACCOUNT_ID}', '{DEFAULT_ACCOUNT_EMAIL}', true, NOW(), NOW())
        ON CONFLICT (id) DO NOTHING
        """
    )
    op.drop_constraint(
        "persons_canonical_name_key",
        "persons",
        schema="formegot",
        type_="unique",
    )

    for table_name in SCOPED_TABLES:
        op.add_column(
            table_name,
            sa.Column("account_id", sa.UUID(), nullable=True),
            schema="formegot",
        )
        op.execute(
            f"""
            UPDATE formegot.{table_name}
            SET account_id = '{DEFAULT_ACCOUNT_ID}'
            WHERE account_id IS NULL
            """
        )
        op.alter_column(
            table_name,
            "account_id",
            nullable=False,
            schema="formegot",
        )
        op.create_foreign_key(
            f"fk_{table_name}_account_id_accounts",
            table_name,
            "accounts",
            ["account_id"],
            ["id"],
            source_schema="formegot",
            referent_schema="formegot",
            ondelete="CASCADE",
        )
        op.create_index(
            f"ix_{table_name}_account_id",
            table_name,
            ["account_id"],
            schema="formegot",
        )

    op.create_unique_constraint(
        "uq_persons_account_canonical_name",
        "persons",
        ["account_id", "canonical_name"],
        schema="formegot",
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_persons_account_canonical_name",
        "persons",
        schema="formegot",
        type_="unique",
    )

    for table_name in reversed(SCOPED_TABLES):
        op.drop_index(
            f"ix_{table_name}_account_id",
            table_name=table_name,
            schema="formegot",
        )
        op.drop_constraint(
            f"fk_{table_name}_account_id_accounts",
            table_name,
            schema="formegot",
            type_="foreignkey",
        )
        op.drop_column(table_name, "account_id", schema="formegot")

    op.create_unique_constraint(
        "persons_canonical_name_key",
        "persons",
        ["canonical_name"],
        schema="formegot",
    )
    op.drop_index("ix_accounts_email", table_name="accounts", schema="formegot")
    op.drop_table("accounts", schema="formegot")
