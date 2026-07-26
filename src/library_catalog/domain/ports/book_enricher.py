from typing import Protocol


class BookEnricherProtocol(Protocol):
    """Интерфейс получения дополнительных данных о книге."""

    async def enrich(
            self,
            title: str,
            author: str,
            isbn: str | None = None,
    ) -> dict:
        ...