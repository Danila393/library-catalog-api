from typing import Any

import httpx

from ...domain.dto.book import BookExtra
from ...domain.exceptions import OpenLibraryException, OpenLibraryTimeoutException
from ..base.base_client import BaseApiClient


class OpenLibraryClient(BaseApiClient):
    """Клиент для Open Library API."""

    def __init__(
        self,
        base_url: str = "https://openlibrary.org",
        timeout: float = 10.0,
        max_connections: int = 20,
        max_keepalive_connections: int = 10,
    ) -> None:
        super().__init__(
            base_url,
            timeout=timeout,
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
        )

    def client_name(self) -> str:
        return "openlibrary"

    async def search_by_isbn(self, isbn: str) -> BookExtra:
        """Поиск книги по ISBN."""
        try:
            data = await self._get("/search.json", params={"isbn": isbn, "limit": 1})

            docs = data.get("docs", [])
            if not docs:
                return {}

            return self._extract_book_data(docs[0])

        except httpx.TimeoutException as exc:
            raise OpenLibraryTimeoutException(self.timeout) from exc
        except httpx.HTTPError as exc:
            raise OpenLibraryException(str(exc)) from exc

    async def search_by_title_author(
        self,
        title: str,
        author: str,
    ) -> BookExtra:
        """Поиск по названию и автору."""
        try:
            data = await self._get(
                "/search.json", params={"title": title, "author": author, "limit": 1}
            )

            docs = data.get("docs", [])
            if not docs:
                return {}

            return self._extract_book_data(docs[0])

        except httpx.TimeoutException as exc:
            raise OpenLibraryTimeoutException(self.timeout) from exc
        except httpx.HTTPError as exc:
            raise OpenLibraryException(str(exc)) from exc

    async def enrich(
        self,
        title: str,
        author: str,
        isbn: str | None = None,
    ) -> BookExtra:
        """
        Обогатить данные книги.
        Сначала пытается найти по ISBN, затем по title+author.
        """
        if isbn:
            data = await self.search_by_isbn(isbn)
            if data:
                return data

        return await self.search_by_title_author(title, author)

    def _extract_book_data(self, doc: dict[str, Any]) -> BookExtra:
        """Извлечь нужные поля из ответа Open Library."""
        result: BookExtra = {}

        if cover_id := doc.get("cover_i"):
            result["cover_url"] = self._get_cover_url(cover_id)

        if subjects := doc.get("subject"):
            result["subjects"] = subjects[:10]  # Первые 10

        if publisher := doc.get("publisher"):
            result["publisher"] = publisher[0] if publisher else None

        if language := doc.get("language"):
            result["language"] = language[0] if language else None

        if ratings := doc.get("ratings_average"):
            result["rating"] = ratings

        return result

    def _get_cover_url(self, cover_id: int | None) -> str | None:
        """Получить URL обложки."""
        if not cover_id:
            return None
        return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
