from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# ★ Base は base.py から正しく import
from backend.models.base.base import Base

# Alembic が使う MetaData
target_metadata = Base.metadata
# --- models import（Alembic に存在を知らせるため） ---

# person
import backend.models.person.person
import backend.models.person.person_profile
import backend.models.person.person_tag

# community
import backend.models.community.community
import backend.models.community.community_tree

# membership
import backend.models.membership.membership

# interaction
import backend.models.interaction.interaction
import backend.models.interaction.topic
import backend.models.interaction.interaction_tag

# task
import backend.models.task.relationship_task
import backend.models.task.task_history

# reminder
import backend.models.reminder.reminder
import backend.models.reminder.trigger

# insight
import backend.models.insight.insight

# network
import backend.models.network.relation

# tag
import backend.models.tag.tag

# ai
import backend.models.ai.parsed_note
import backend.models.ai.ai_metadata

# calendar
import backend.models.calendar.calendar_event
import backend.models.calendar.meeting_snapshot


# Alembic Config
config = context.config

# Logging 設定
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# --- スキーマ制御（formegot のみ対象） ---
def include_name(name, type_, parent_names):
    # Alembic管理テーブルは常に除外
    if name == "alembic_version":
        return False

    if type_ == "schema":
        return name == "formegot"

    schema = parent_names.get("schema_name")
    return schema == "formegot"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        include_schemas=True,
        include_name=include_name,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_name=include_name,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
