"""Alembic environment for BM-Anything business database.

URL resolution priority:
1. ``-x bm_db_url=...`` command-line override
2. ``BM_DATABASE_URL`` environment variable
3. ``BMSettings.effective_database_url()`` (derived from BM_HOME / OS data dir)

This env.py only manages the BM business schema. The execution engine
(Hatchet / Temporal / DBOS, chosen in P3) owns ``execution.sqlite3`` and
MUST NOT share this Alembic history.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from bm.config.settings import BMSettings
from bm.infrastructure.database.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _resolve_url() -> str:
    x_args = context.get_x_argument(as_dictionary=True)
    if "bm_db_url" in x_args:
        return x_args["bm_db_url"]
    settings = BMSettings()
    return settings.effective_database_url()


def run_migrations_offline() -> None:
    context.configure(
        url=_resolve_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = _resolve_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=connection.dialect.name == "sqlite",
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
