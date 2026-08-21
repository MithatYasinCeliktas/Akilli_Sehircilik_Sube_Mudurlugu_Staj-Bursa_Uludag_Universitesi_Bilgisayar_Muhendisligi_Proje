import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.core.config import settings
from app.models.base import Base
# Tüm modellerin Alembic tarafından tespiti için import edilmesi
from app.models.user import User  # noqa: F401
from app.models.unit import Unit  # noqa: F401
from app.models.report import ActivityReport, ReportItem  # noqa: F401
from app.models.report_share import ReportShare  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.institution import Institution  # noqa: F401
from app.models.system_log import SystemLog  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Offline modda migrasyon çalıştırma."""
    url = settings.ASYNC_SQLALCHEMY_DATABASE_URI
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Asenkron bağlantı ile online migrasyon çalıştırma."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = str(settings.ASYNC_SQLALCHEMY_DATABASE_URI)

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Online modda migrasyon çalıştırma."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()