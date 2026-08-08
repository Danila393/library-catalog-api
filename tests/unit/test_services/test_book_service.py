from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from library_catalog.domain.dto.book import BookCreateDTO, BookUpdateDTO
from library_catalog.domain.exceptions import (
    BookAlreadyExistsException,
    BookNotFoundException,
    InvalidYearException,
    OpenLibraryTimeoutException,
)
from library_catalog.domain.services.book_service import BookService


def _make_stored_book(
    book_data: BookCreateDTO,
    **overrides: object,
) -> SimpleNamespace:
    now = datetime.now(UTC)
    values: dict[str, object] = {
        "book_id": uuid4(),
        "title": book_data.title,
        "author": book_data.author,
        "year": book_data.year,
        "genre": book_data.genre,
        "pages": book_data.pages,
        "available": True,
        "isbn": book_data.isbn,
        "description": book_data.description,
        "extra": None,
        "created_at": now,
        "updated_at": now,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


@pytest.fixture
def book_data() -> BookCreateDTO:
    return BookCreateDTO(
        title="Clean Code",
        author="Robert Martin",
        year=2008,
        genre="Programming",
        pages=464,
        isbn="9780132350884",
        description="A Handbook of Agile Software Craftsmanship",
    )


@pytest.fixture
def repository() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def enricher() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def service(repository: AsyncMock, enricher: AsyncMock) -> BookService:
    return BookService(repository, enricher)


@pytest.mark.asyncio
async def test_create_book_continues_when_openlibrary_times_out(
    book_data: BookCreateDTO,
    repository: AsyncMock,
    enricher: AsyncMock,
    service: BookService,
) -> None:
    stored_book = _make_stored_book(book_data)
    repository.find_by_isbn.return_value = None
    repository.create.return_value = stored_book
    enricher.enrich.side_effect = OpenLibraryTimeoutException(timeout=1.0)

    result = await service.create_book(book_data)

    assert result.book_id == stored_book.book_id
    assert result.extra is None
    repository.create.assert_awaited_once_with(
        title=book_data.title,
        author=book_data.author,
        year=book_data.year,
        genre=book_data.genre,
        pages=book_data.pages,
        isbn=book_data.isbn,
        description=book_data.description,
        extra=None,
    )


@pytest.mark.asyncio
async def test_create_book_rejects_duplicate_isbn(
    book_data: BookCreateDTO,
    repository: AsyncMock,
    enricher: AsyncMock,
    service: BookService,
) -> None:
    repository.find_by_isbn.return_value = object()

    with pytest.raises(BookAlreadyExistsException) as exc_info:
        await service.create_book(book_data)

    assert exc_info.value.status_code == 409
    assert book_data.isbn is not None
    assert book_data.isbn in exc_info.value.message
    enricher.enrich.assert_not_awaited()
    repository.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_book_rejects_future_year(
    book_data: BookCreateDTO,
    repository: AsyncMock,
    enricher: AsyncMock,
    service: BookService,
) -> None:
    future_book_data = book_data.model_copy(
        update={"year": datetime.now(UTC).year + 1},
    )

    with pytest.raises(InvalidYearException) as exc_info:
        await service.create_book(future_book_data)

    assert exc_info.value.status_code == 400
    repository.find_by_isbn.assert_not_awaited()
    enricher.enrich.assert_not_awaited()
    repository.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_book_raises_when_book_is_missing(
    repository: AsyncMock,
    service: BookService,
) -> None:
    book_id = uuid4()
    repository.get_by_id.return_value = None

    with pytest.raises(BookNotFoundException) as exc_info:
        await service.get_book(book_id)

    assert exc_info.value.status_code == 404
    assert str(book_id) in exc_info.value.message


@pytest.mark.asyncio
async def test_update_book_passes_only_changed_fields(
    book_data: BookCreateDTO,
    repository: AsyncMock,
    service: BookService,
) -> None:
    existing_book = _make_stored_book(book_data)
    updated_title = "Clean Architecture"
    updated_book = _make_stored_book(
        book_data,
        book_id=existing_book.book_id,
        title=updated_title,
        created_at=existing_book.created_at,
    )
    repository.get_by_id.return_value = existing_book
    repository.update.return_value = updated_book

    result = await service.update_book(
        existing_book.book_id,
        BookUpdateDTO(title=updated_title),
    )

    assert result.title == updated_title
    repository.update.assert_awaited_once_with(
        existing_book.book_id,
        title=updated_title,
    )


@pytest.mark.asyncio
async def test_delete_book_raises_when_book_is_missing(
    repository: AsyncMock,
    service: BookService,
) -> None:
    book_id = uuid4()
    repository.delete.return_value = False

    with pytest.raises(BookNotFoundException) as exc_info:
        await service.delete_book(book_id)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_search_books_passes_filters_and_returns_total(
    book_data: BookCreateDTO,
    repository: AsyncMock,
    service: BookService,
) -> None:
    stored_book = _make_stored_book(book_data)
    repository.find_by_filters.return_value = [stored_book]
    repository.count_by_filters.return_value = 1

    books, total = await service.search_books(
        title="Clean",
        genre="Programming",
        available=True,
        limit=10,
        offset=20,
    )

    assert total == 1
    assert len(books) == 1
    assert books[0].book_id == stored_book.book_id
    repository.find_by_filters.assert_awaited_once_with(
        title="Clean",
        author=None,
        genre="Programming",
        year=None,
        available=True,
        limit=10,
        offset=20,
    )
    repository.count_by_filters.assert_awaited_once_with(
        title="Clean",
        author=None,
        genre="Programming",
        year=None,
        available=True,
    )
