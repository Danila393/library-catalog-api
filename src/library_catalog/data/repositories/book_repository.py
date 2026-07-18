from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .base_repository import BaseRepository
from ..models.book import Book


class BookRepository(BaseRepository[Book]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Book)


    async def find_by_filters(
        self,
        title: str | None = None,
        author: str | None = None,
        genre: str | None = None,
        year: int | None = None,
        available: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Book]:
        """Поиск книг с фильтрацией"""
        stmt = select(Book)

        if title:
            stmt = stmt.where(Book.title.ilike(f"%{title}%"))

        if author:
            stmt = stmt.where(Book.author.ilike(f"%{author}%"))

        if genre is not None:
            stmt = stmt.where(Book.genre == genre)

        if year:
            stmt = stmt.where(Book.year == year)

        if available is not None:
            stmt = stmt.where(Book.available == available)

        if limit is not None:
            stmt = stmt.limit(limit)

        if offset is not None:
            stmt = stmt.offset(offset)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())


    async def find_by_isbn(self, isbn: str) -> Book | None:
        """Найти книгу по ISBN"""
        stmt = select(Book)

        if isbn is not None:
            stmt = stmt.where(Book.isbn == isbn)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


    async def count_by_filters(
        self,
        title: str | None = None,
        author: str | None = None,
        genre: str | None = None,
        year: int | None = None,
        available: bool | None = None,
    ) -> int:

        stmt = select(func.count()).select_from(Book)

        if title:
            stmt = stmt.where(Book.title.ilike(f"%{title}%"))

        if author:
            stmt = stmt.where(Book.author.ilike(f"%{author}%"))

        if genre is not None:
            stmt = stmt.where(Book.genre == genre)

        if year:
            stmt = stmt.where(Book.year == year)

        if available is not None:
            stmt = stmt.where(Book.available == available)

        result = await self.session.execute(stmt)
        return result.scalar() or 0
