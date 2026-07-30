from typing import TypeVar

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from ...domain.exceptions import BookAlreadyExistsException
from ..models.book import Book
from .base_repository import BaseRepository

_SelectRowT = TypeVar("_SelectRowT", bound=tuple[object, ...])


class BookRepository(BaseRepository[Book]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Book)

    async def create(self, **kwargs: object) -> Book:
        try:
            return await super().create(**kwargs)
        except IntegrityError as exc:
            isbn = kwargs.get("isbn")
            sqlstate = getattr(exc.orig, "sqlstate", None) or getattr(
                exc.orig, "pgcode", None
            )

            if sqlstate == "23505" and isinstance(isbn, str):
                raise BookAlreadyExistsException(isbn) from exc

            raise

    @staticmethod
    def _apply_filters(
        stmt: Select[_SelectRowT],
        *,
        title: str | None = None,
        author: str | None = None,
        genre: str | None = None,
        year: int | None = None,
        available: bool | None = None,
    ) -> Select[_SelectRowT]:
        """Применить фильтры книг к SQL-запросу."""

        if title:
            stmt = stmt.where(Book.title.ilike(f"%{title}%"))

        if author:
            stmt = stmt.where(Book.author.ilike(f"%{author}%"))

        if genre is not None:
            stmt = stmt.where(Book.genre == genre)

        if year is not None:
            stmt = stmt.where(Book.year == year)

        if available is not None:
            stmt = stmt.where(Book.available == available)

        return stmt

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
        stmt = self._apply_filters(
            select(Book),
            title=title,
            author=author,
            genre=genre,
            year=year,
            available=available,
        )

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

        stmt = self._apply_filters(
            select(func.count()).select_from(Book),
            title=title,
            author=author,
            genre=genre,
            year=year,
            available=available,
        )

        result = await self.session.execute(stmt)
        return result.scalar() or 0
