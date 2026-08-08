from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from library_catalog.data.models.book import Book
from library_catalog.data.repositories.book_repository import BookRepository
from library_catalog.domain.exceptions import BookAlreadyExistsException


class _UniqueViolation(Exception):
    sqlstate = "23505"


@pytest.mark.asyncio
async def test_update_translates_duplicate_isbn_to_domain_exception() -> None:
    book_id = uuid4()
    duplicate_isbn = "9780132350884"
    stored_book = SimpleNamespace(isbn="9780201616224")

    session = AsyncMock(spec=AsyncSession)
    session.get.return_value = stored_book
    session.flush.side_effect = IntegrityError(
        statement="UPDATE books SET isbn=:isbn",
        params={"isbn": duplicate_isbn},
        orig=_UniqueViolation(),
    )
    repository = BookRepository(session)

    with pytest.raises(BookAlreadyExistsException) as exc_info:
        await repository.update(book_id, isbn=duplicate_isbn)

    assert exc_info.value.status_code == 409
    assert duplicate_isbn in exc_info.value.message
    session.get.assert_awaited_once_with(Book, book_id)
    session.refresh.assert_not_awaited()
