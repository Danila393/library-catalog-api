from collections.abc import AsyncIterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from library_catalog.api.dependencies import get_book_service
from library_catalog.domain.dto.book import BookDTO
from library_catalog.domain.exceptions import (
    BookAlreadyExistsException,
    BookNotFoundException,
)
from library_catalog.main import app


@pytest.fixture
def book_service_mock() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def sample_book() -> BookDTO:
    now = datetime.now(UTC)
    return BookDTO(
        book_id=uuid4(),
        title="Clean Code",
        author="Robert Martin",
        year=2008,
        genre="Programming",
        pages=464,
        available=True,
        isbn="9780132350884",
        description="A Handbook of Agile Software Craftsmanship",
        extra=None,
        created_at=now,
        updated_at=now,
    )


@pytest_asyncio.fixture
async def api_client(
    book_service_mock: AsyncMock,
) -> AsyncIterator[AsyncClient]:
    def override_book_service() -> AsyncMock:
        return book_service_mock

    app.dependency_overrides[get_book_service] = override_book_service
    transport = ASGITransport(
        app=app,
        raise_app_exceptions=False,
    )

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_book_service, None)


@pytest.mark.asyncio
async def test_create_book_returns_201(
    api_client: AsyncClient,
    book_service_mock: AsyncMock,
    sample_book: BookDTO,
) -> None:
    book_service_mock.create_book.return_value = sample_book
    payload = {
        "title": sample_book.title,
        "author": sample_book.author,
        "year": sample_book.year,
        "genre": sample_book.genre,
        "pages": sample_book.pages,
        "isbn": sample_book.isbn,
        "description": sample_book.description,
    }

    response = await api_client.post("/api/v1/books/", json=payload)

    assert response.status_code == 201
    assert response.json()["book_id"] == str(sample_book.book_id)
    submitted_book = book_service_mock.create_book.await_args.args[0]
    assert submitted_book.title == sample_book.title


@pytest.mark.asyncio
async def test_get_books_applies_filters_and_pagination(
    api_client: AsyncClient,
    book_service_mock: AsyncMock,
    sample_book: BookDTO,
) -> None:
    book_service_mock.search_books.return_value = ([sample_book], 1)

    response = await api_client.get(
        "/api/v1/books/",
        params={
            "title": "Clean",
            "available": "true",
            "page": 1,
            "page_size": 10,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["page"] == 1
    assert body["page_size"] == 10
    assert body["pages"] == 1
    assert body["items"][0]["book_id"] == str(sample_book.book_id)
    book_service_mock.search_books.assert_awaited_once_with(
        title="Clean",
        author=None,
        genre=None,
        year=None,
        available=True,
        limit=10,
        offset=0,
    )


@pytest.mark.asyncio
async def test_get_missing_book_returns_404(
    api_client: AsyncClient,
    book_service_mock: AsyncMock,
) -> None:
    book_id = uuid4()
    book_service_mock.get_book.side_effect = BookNotFoundException(book_id)

    response = await api_client.get(f"/api/v1/books/{book_id}")

    assert response.status_code == 404
    assert str(book_id) in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_duplicate_isbn_returns_409(
    api_client: AsyncClient,
    book_service_mock: AsyncMock,
) -> None:
    book_id = uuid4()
    duplicate_isbn = "9780132350884"
    book_service_mock.update_book.side_effect = BookAlreadyExistsException(
        duplicate_isbn
    )

    response = await api_client.patch(
        f"/api/v1/books/{book_id}",
        json={"isbn": duplicate_isbn},
    )

    assert response.status_code == 409
    assert duplicate_isbn in response.json()["detail"]


@pytest.mark.asyncio
async def test_invalid_page_size_returns_422(
    api_client: AsyncClient,
    book_service_mock: AsyncMock,
) -> None:
    response = await api_client.get(
        "/api/v1/books/",
        params={"page_size": 101},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Request validation failed"
    book_service_mock.search_books.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_book_returns_204(
    api_client: AsyncClient,
    book_service_mock: AsyncMock,
) -> None:
    book_id = uuid4()

    response = await api_client.delete(f"/api/v1/books/{book_id}")

    assert response.status_code == 204
    assert response.content == b""
    book_service_mock.delete_book.assert_awaited_once_with(book_id)
