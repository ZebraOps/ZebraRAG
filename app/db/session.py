"""
数据库会话管理
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import Settings

# 创建临时配置实例（用于数据库引擎初始化）
_settings = Settings()


# 同步引擎（用于Alembic迁移）
engine = create_engine(
    _settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    echo=False
)

# 异步引擎（用于FastAPI应用）
async_engine = create_async_engine(
    _settings.ASYNC_SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    echo=False
)

# 会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# 基类
Base = declarative_base()


def get_db():
    """同步数据库会话依赖"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    """异步数据库会话依赖"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
