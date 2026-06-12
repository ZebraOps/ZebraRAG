"""
Alembic环境配置
"""
from logging.config import fileConfig
from sqlalchemy import engine_from_connection, pool
from alembic import context
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.db.session import Base
from app.models import *  # 导入所有模型

# Alembic配置对象
config = context.config

# 设置数据库URL
config.set_main_option(
    'sqlalchemy.url',
    f"postgresql://{os.getenv('PG_USER', 'postgres')}:{os.getenv('PG_PASSWORD', 'postgres123')}"
    f"@{os.getenv('PG_SERVER', '192.168.192.87:5432')}/{os.getenv('PG_DB', 'zebra_rag')}"
)

# 日志配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# MetaData对象
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式运行迁移"""
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
    """在线模式运行迁移"""
    connectable = engine_from_connection(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
