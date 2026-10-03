"""
Async database engine and session management.

Uses SQLAlchemy 2.0 async engine with asyncpg driver.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

# Async engine for application use
is_sqlite = settings.DATABASE_URL.startswith("sqlite")
engine_kwargs = {"echo": settings.DEBUG}
if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs.update({
        "pool_size": 20,
        "max_overflow": 10,
        "pool_pre_ping": True,
        "pool_recycle": 300,
    })

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

# Async session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def get_db() -> AsyncSession:
    """
    FastAPI dependency that provides an async database session.
    The session is committed on success and rolled back on exception.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create database tables. Used for development/testing only."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
