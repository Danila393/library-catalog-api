from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import settings


class Base(DeclarativeBase):
    """Тут в будущем будут таблицы"""

    pass


engine = create_async_engine(
    settings.database_url_str,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_pool_max_overflow,
    pool_timeout=settings.database_pool_timeout,
    pool_recycle=settings.database_pool_recycle,
    echo=settings.debug,
)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            # Отменяем изменения в БД, если запрос завершился ошибкой.
            await session.rollback()
            raise
        finally:
            await session.close()  # Закрываем соединение чтобы не перегружать БД


async def dispose_engine() -> None:
    """Закрыть все соединения с БД."""
    await engine.dispose()
