"""cascade search documents when person is deleted

Revision ID: 4f1c2e9a8d30
Revises: 3d8a9c1f2b7e
Create Date: 2026-05-19 00:10:00.000000
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "4f1c2e9a8d30"
down_revision: Union[str, Sequence[str], None] = "3d8a9c1f2b7e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "search_documents_person_id_fkey",
        "search_documents",
        schema="formegot",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "search_documents_person_id_fkey",
        "search_documents",
        "persons",
        ["person_id"],
        ["id"],
        source_schema="formegot",
        referent_schema="formegot",
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "search_documents_person_id_fkey",
        "search_documents",
        schema="formegot",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "search_documents_person_id_fkey",
        "search_documents",
        "persons",
        ["person_id"],
        ["id"],
        source_schema="formegot",
        referent_schema="formegot",
        ondelete="SET NULL",
    )
