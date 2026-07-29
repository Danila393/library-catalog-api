from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import settings


class Base(DeclarativeBase):
    """ Тут в будущем будут таблицы"""
    pass


engine = create_async_engine(
    settings.database_url_str,
    pool_size=settings.database_pool_size,
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
        except Exception:
            await session.rollback() # Отменяем изменения в БД, если что-то пошло не так
            raise
        finally:
            await session.close() # Закрываем соединение чтобы не перегружать БД


async def dispose_engine() -> None:
    """Закрыть все соединения с БД."""
    await engine.dispose()