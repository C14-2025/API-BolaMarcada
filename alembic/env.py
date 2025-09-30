from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os, sys


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


APP_DIR = os.path.join(PROJECT_ROOT, "app")
if os.path.isdir(APP_DIR) and APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


from core.config import settings
from core.database import Base


from models.models import (
    User,
    SportsCenter,
    Review,
    Field,
    Availability,
    Booking,
)

# === Alembic config ===
config = context.config

# sobrescreve a URL do ini pela URL montada via Settings (.env)
config.set_main_option("sqlalchemy.url", settings.assemble_db_connection())

if config.config_file_name is not None:

    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()