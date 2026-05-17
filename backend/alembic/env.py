import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.database.base import Base

# Import all models here so Alembic can discover them
import app.models.user  # noqa
import app.models.farm  # noqa
import app.models.soil  # noqa
import app.models.weather  # noqa
import app.models.satellite  # noqa
import app.models.prediction  # noqa
import app.models.schedule  # noqa
import app.models.model_log  # noqa
import app.models.sensor  # noqa

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Override sqlalchemy.url with the one from our settings
config.set_main_option("sqlalchemy.url", settings.database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def include_object(object, name, type_, reflected, compare_to):
    """
    Ignore PostGIS and Tiger spatial tables during autogenerate.
    """
    if type_ == "table" and name in (
        "spatial_ref_sys", "topology", "layer", "loader_lookuptables",
        "loader_platform", "loader_variables", "geocode_settings",
        "geocode_settings_default", "direction_lookup", "secondary_unit_lookup",
        "state_lookup", "street_type_lookup", "zip_lookup_all", "zip_lookup_base",
        "zip_lookup", "countysub_lookup", "county_lookup", "place_lookup",
        "zip_state", "zip_state_loc", "pagc_gaz", "pagc_lex", "pagc_rules",
        "addr", "addrfeat", "bg", "county", "cousub", "edges", "faces",
        "featnames", "place", "state", "tabblock", "tabblock20", "tract", "zcta5"
    ):
        return False
    return True

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, include_object=include_object)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
