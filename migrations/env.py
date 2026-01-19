import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool, text
from sqlmodel import SQLModel

# ================================
# 1. パス設定：backend フォルダをインポート対象に加える
# ================================
# env.py (migrations/) の親の親がプロジェクトルート
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# ================================
# 2. モデルのインポート
# SQLModel.metadata にテーブル情報を登録するために必要
# ================================
# 各 package の __init__.py で SQLModel を継承したクラスを import しておく必要があります
try:
    from models import (
        base,
        person,
        community,
        membership,
        interaction,
        task,
        insight,
        network,
        tag,
        reminder,
        ai,
        calendar,
    )
except ImportError as e:
    print(f"Import Error: {e}")
    print(f"Current sys.path: {sys.path}")
    raise

# ================================
# 3. Alembic 設定とメタデータ
# ================================
config = context.config

# ログ設定
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# SQLModel の全メタデータを対象にする
target_metadata = SQLModel.metadata

# DB URL（環境変数があれば上書き）
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    config.set_main_option("sqlalchemy.url", DATABASE_URL.replace("postgres://", "postgresql://"))

# ================================
# 4. マイグレーション関数
# ================================

def run_migrations_offline() -> None:
    """Offline mode: SQLを出力するモード"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        # 指定されたスキーマを使用する場合
        version_table_schema="forgetmenot",
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Online mode: 実際にDBに接続するモード"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # PostgreSQL のスキーマを作成・設定
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS forgetmenot"))
        connection.execute(text("SET search_path TO forgetmenot"))
        connection.commit() # スキーマ設定を確定

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            version_table_schema="forgetmenot",
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()