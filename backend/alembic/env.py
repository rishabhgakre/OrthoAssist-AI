"""
Alembic environment — wired to the app's own settings and models so there
is exactly one source of truth for the DB connection string and the schema,
instead of Alembic maintaining its own separate copy of either.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Make "app.*" importable when alembic is run from backend/ (prepend_sys_path
# in alembic.ini already adds "." to sys.path, i.e. the backend/ directory).
from app.core.config import settings
from app.core.database import Base
from app.models import models  # noqa: F401 — registers every model on Base.metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Single source of truth: the same DATABASE_URL env var the running app
# uses, not a separately-maintained value in alembic.ini.
config.set_main_option(
    "sqlalchemy.url",
    settings.DATABASE_URL.replace("%", "%%")
)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Generate SQL scripts without a live DB connection (`alembic upgrade
    head --sql`) — not typically needed for this project, but kept for
    completeness since it's the Alembic-generated default."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """The normal path: connect to the real database and apply migrations."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
