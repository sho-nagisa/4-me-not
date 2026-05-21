"""add memory tasks and calendar participants

Revision ID: 6b7d8e9f0a12
Revises: 4f1c2e9a8d30
Create Date: 2026-05-21 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "6b7d8e9f0a12"
down_revision: Union[str, Sequence[str], None] = "4f1c2e9a8d30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DEFAULT_ACCOUNT_ID = "00000000-0000-0000-0000-000000000001"


def upgrade() -> None:
    op.add_column(
        "calendar_events",
        sa.Column("account_id", sa.UUID(), nullable=True),
        schema="formegot",
    )
    op.add_column(
        "calendar_events",
        sa.Column("description", sa.Text(), nullable=True),
        schema="formegot",
    )
    op.add_column(
        "calendar_events",
        sa.Column("location", sa.String(length=255), nullable=True),
        schema="formegot",
    )
    op.execute(
        f"""
        UPDATE formegot.calendar_events
        SET account_id = '{DEFAULT_ACCOUNT_ID}'
        WHERE account_id IS NULL
        """
    )
    op.alter_column("calendar_events", "account_id", nullable=False, schema="formegot")
    op.create_foreign_key(
        "fk_calendar_events_account_id_accounts",
        "calendar_events",
        "accounts",
        ["account_id"],
        ["id"],
        source_schema="formegot",
        referent_schema="formegot",
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_calendar_events_account_start",
        "calendar_events",
        ["account_id", "start_at"],
        schema="formegot",
    )

    op.create_table(
        "tasks",
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.Integer(), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=True),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=True),
        sa.Column("is_candidate", sa.Boolean(), nullable=False),
        sa.Column("candidate_status", sa.String(length=30), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
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
        "ix_tasks_account_status_due",
        "tasks",
        ["account_id", "candidate_status", "status", "due_at"],
        schema="formegot",
    )
    op.create_index(
        "ix_tasks_account_source",
        "tasks",
        ["account_id", "source_type", "source_id"],
        schema="formegot",
    )

    op.create_table(
        "task_links",
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column("task_id", sa.UUID(), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("target_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["formegot.accounts.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["formegot.tasks.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "task_id",
            "target_type",
            "target_id",
            "role",
            name="uq_task_links_target_role",
        ),
        schema="formegot",
    )
    op.create_index(
        "ix_task_links_account_target",
        "task_links",
        ["account_id", "target_type", "target_id"],
        schema="formegot",
    )
    op.create_index(
        "ix_task_links_task",
        "task_links",
        ["task_id"],
        schema="formegot",
    )

    op.create_table(
        "event_participants",
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column("calendar_event_id", sa.UUID(), nullable=False),
        sa.Column("person_id", sa.UUID(), nullable=True),
        sa.Column("display_name", sa.String(length=100), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("is_inferred", sa.Boolean(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["formegot.accounts.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["calendar_event_id"],
            ["formegot.calendar_events.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["person_id"],
            ["formegot.persons.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "calendar_event_id",
            "person_id",
            "email",
            name="uq_event_participants_identity",
        ),
        schema="formegot",
    )
    op.create_index(
        "ix_event_participants_account_event",
        "event_participants",
        ["account_id", "calendar_event_id"],
        schema="formegot",
    )
    op.create_index(
        "ix_event_participants_person",
        "event_participants",
        ["person_id"],
        schema="formegot",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_event_participants_person",
        table_name="event_participants",
        schema="formegot",
    )
    op.drop_index(
        "ix_event_participants_account_event",
        table_name="event_participants",
        schema="formegot",
    )
    op.drop_table("event_participants", schema="formegot")

    op.drop_index("ix_task_links_task", table_name="task_links", schema="formegot")
    op.drop_index(
        "ix_task_links_account_target",
        table_name="task_links",
        schema="formegot",
    )
    op.drop_table("task_links", schema="formegot")

    op.drop_index(
        "ix_tasks_account_source",
        table_name="tasks",
        schema="formegot",
    )
    op.drop_index(
        "ix_tasks_account_status_due",
        table_name="tasks",
        schema="formegot",
    )
    op.drop_table("tasks", schema="formegot")

    op.drop_index(
        "ix_calendar_events_account_start",
        table_name="calendar_events",
        schema="formegot",
    )
    op.drop_constraint(
        "fk_calendar_events_account_id_accounts",
        "calendar_events",
        schema="formegot",
        type_="foreignkey",
    )
    op.drop_column("calendar_events", "location", schema="formegot")
    op.drop_column("calendar_events", "description", schema="formegot")
    op.drop_column("calendar_events", "account_id", schema="formegot")
