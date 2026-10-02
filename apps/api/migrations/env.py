from logging.config import fileConfig
import os
from alembic import context
from sqlalchemy import create_engine, pool
from app.core.config import Settings
from app.db.models import Base

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)
url = config.attributes.get('database_url') or os.environ.get('AP_DATABASE_URL') or Settings.load().database_url
metadata = Base.metadata

if context.is_offline_mode():
    context.configure(url=url, target_metadata=metadata, literal_binds=True, dialect_opts={'paramstyle':'named'})
    with context.begin_transaction():
        context.run_migrations()
else:
    with create_engine(url, poolclass=pool.NullPool).connect() as connection:
        context.configure(connection=connection, target_metadata=metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()
