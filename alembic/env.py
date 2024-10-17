import os
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from alembic import context
from dotenv import load_dotenv
from config import DATABASE_URL

# Загрузка переменных окружения из файла .env
load_dotenv()

# Настройка конфигурации Alembic
config = context.config

# Установка значения sqlalchemy.url из переменной окружения
database_url = DATABASE_URL
if not isinstance(database_url, str):
    raise TypeError("DATABASE_URL must be a string")
config.set_main_option('sqlalchemy.url', database_url)

# Настройка логирования
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Импорт моделей для 'autogenerate' поддержки
from models.dbs.models import User
target_metadata = User.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(
        connection=connection, target_metadata=target_metadata
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = create_async_engine(
        DATABASE_URL,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

if context.is_offline_mode():
    run_migrations_offline()
else:
    import asyncio
    asyncio.run(run_migrations_online())