from typing import Generic, TypeVar, Type
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


T = TypeVar("T")

class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model


    async def create(self, **kwargs) -> T:
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush() # Отправляем INSERT в БД без завершения транзакции
        await self.session.refresh(instance) # обновляем обьект
        return instance # вовзращаем обновлённый обьект


    async def get_by_id(self, id: UUID) -> T | None:
        """Получить запись по ID"""
        return await self.session.get(self.model, id)


    async def update(self, id: UUID, **kwargs) -> T | None:
        instance = await self.get_by_id(id)
        # если ID нету - возвращаем None
        if instance is None:
            return None

        for key, value in kwargs.items():
            setattr(instance, key, value)

        await self.session.flush()
        await self.session.refresh(instance)

        return instance


    async def delete(self, id: UUID) -> bool:
        """Удалить запись"""
        instance = await self.get_by_id(id)
        if instance is None:
            return False

        await self.session.delete(instance)
        await self.session.flush()
        return True

    async def get_all(
            self,
            limit: int = 100,
            offset: int = 0,
    ) -> list[T]:
        """Получить все записи с пагинацией."""
        stmt = select(self.model).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())