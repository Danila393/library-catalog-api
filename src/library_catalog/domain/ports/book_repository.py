from collections.abc import Sequence
from datetime import datetime
from typing import Protocol
from uuid import UUID


class BookRecord(Protocol):
    """Данные книги, возвращаемые репозиторием."""

    book_id: UUID
    title: str
    author: str
    year: int
    genre: str
    pages: int
    available: bool
    isbn: str | None
    description: str | None
    extra: dict | None
    created_at: datetime
    updated_at: datetime


class BookRepositoryProtocol(Protocol):
    """Интерфейс репозитория книг."""


    async def create(self, **kwargs: object) -> BookRecord:
        ...

    async def get_by_id(self, id: UUID) -> BookRecord | None:
        ...

    async def update(
            self,
            id: UUID,
            **kwargs: object,
    ) -> BookRecord | None:
        ...

    async def delete(self, id: UUID) -> bool:
        ...

    async def find_by_isbn(self, isbn: str) -> BookRecord | None:
        ...

    async def find_by_filters(
            self,
            title: str | None = None,
            author: str | None = None,
            genre: str | None = None,
            year: int | None = None,
            available: bool | None = None,
            limit: int = 20,
            offset: int = 0,
    ) -> Sequence[BookRecord]:
        ...

    async def count_by_filters(
            self,
            title: str | None = None,
            author: str | None = None,
            genre: str | None = None,
            year: int | None = None,
            available: bool | None = None,
    ) -> int:
        ...