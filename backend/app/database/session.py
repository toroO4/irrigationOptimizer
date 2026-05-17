"""
SAR Irrigation Scheduling System — Database Session Management.

Provides:
- Async SQLAlchemy engine with connection pooling
- Async session factory
- FastAPI dependency for database sessions
- Sync engine for Alembic migrations
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Async Engine (for FastAPI application)
# ---------------------------------------------------------------------------
async_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# ---------------------------------------------------------------------------
# Async Session Factory
# ---------------------------------------------------------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# ---------------------------------------------------------------------------
# Sync Engine (for Alembic migrations and scripts)
# ---------------------------------------------------------------------------
sync_engine = create_engine(
    settings.database_sync_url,
    echo=settings.debug,
    pool_pre_ping=True,
)


async def get_db() -> AsyncSession:
    """
    FastAPI dependency that provides a database session.

    Yields an async session and ensures it is closed after the request
    completes, even if an exception occurs.

    Usage in endpoints:
        @router.get("/example")
        async def example(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(SomeModel))
            return result.scalars().all()

    Yields:
        AsyncSession: An active database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize the database by creating all tables.

    Called during application startup. In production, use Alembic
    migrations instead.
    """
    from app.database.base import Base  # noqa: F811

    async with async_engine.begin() as conn:
        # Import all models so they are registered with Base
        import app.models.user  # noqa: F401
        import app.models.farm  # noqa: F401
        import app.models.soil  # noqa: F401
        import app.models.weather  # noqa: F401
        import app.models.satellite  # noqa: F401
        import app.models.prediction  # noqa: F401
        import app.models.schedule  # noqa: F401
        import app.models.model_log  # noqa: F401

        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")


async def close_db() -> None:
    """
    Close the database engine connections.

    Called during application shutdown to cleanly release resources.
    """
    await async_engine.dispose()
    logger.info("Database connections closed")
