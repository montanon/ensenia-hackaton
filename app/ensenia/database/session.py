"""Database session management and initialization.

Provides async SQLAlchemy engine, session factory, and dependency
injection for FastAPI routes.
"""

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.ensenia.core.config import settings
from app.ensenia.database.models import Base

logger = logging.getLogger(__name__)


def _create_engine() -> AsyncEngine:
    """Create a new async engine using current settings."""
    return create_async_engine(
        settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_pre_ping=True,
        echo=settings.debug,
    )


def _create_session_factory(
    bind_engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Create a new async session factory bound to provided engine."""
    return async_sessionmaker(
        bind_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


# Initialize engine and session factory
engine: AsyncEngine = _create_engine()
AsyncSessionLocal: async_sessionmaker[AsyncSession] = _create_session_factory(engine)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI routes to get database session.

    Yields:
        AsyncSession: Database session

    Example:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()

    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database by creating all tables.

    This should be called on application startup.
    For production, use Alembic migrations instead.
    """
    logger.info("Initializing database...")

    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database initialized successfully")


async def close_db() -> None:
    """Close database engine and all connections.

    This should be called on application shutdown.
    """
    logger.info("Closing database connections...")
    await engine.dispose()
    logger.info("Database connections closed")


async def reset_engine() -> None:
    """Dispose current engine and rebuild it with latest settings.

    Useful for tests that override database configuration.
    """
    global engine, AsyncSessionLocal  # noqa: PLW0603
    logger.info("Resetting database engine with updated settings...")
    await engine.dispose()
    engine = _create_engine()
    AsyncSessionLocal = _create_session_factory(engine)
