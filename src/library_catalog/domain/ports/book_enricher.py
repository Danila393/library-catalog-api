from typing import Protocol

from ..dto.book import BookExtra


class BookEnricherProtocol(Protocol):
    """Интерфейс получения дополнительных данных о книге."""

    async def enrich(
        self,
        title: str,
        author: str,
        isbn: str | None = None,
    ) -> BookExtra: ...
