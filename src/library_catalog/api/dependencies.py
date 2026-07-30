from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..data.repositories.book_repository import BookRepository
from ..domain.services.book_service import BookService
from ..external.openlibrary.client import OpenLibraryClient
from ..core.config import settings




# ========== EXTERNAL CLIENTS (Singletons) ==========

@lru_cache
def get_openlibrary_client() -> OpenLibraryClient:
    """
    Получить singleton OpenLibraryClient.

    Декоратор @lru_cache гарантирует, что функция выполнится только один раз.
    FastAPI создаст HTTP-клиент при первом запросе, сохранит его в память
    и будет переиспользовать для всех последующих запросов.
    """
    return OpenLibraryClient(
        base_url=settings.openlibrary_base_url,
        timeout=settings.openlibrary_timeout,
        max_connections=settings.openlibrary_max_connections,
        max_keepalive_connections=(
            settings.openlibrary_max_keepalive_connections
        ),
    )


# ========== REPOSITORIES ==========

async def get_book_repository(
        db: Annotated[AsyncSession, Depends(get_db)]
) -> BookRepository:
    """
    Создать BookRepository для текущей сессии БД.

    FastAPI сам вызовет get_db(), получит сессию для текущего HTTP-запроса,
    и передаст её сюда (в переменную db).
    Создается новый экземпляр репозитория для каждого запроса пользователя.
    """
    return BookRepository(db)


# ========== SERVICES ==========

async def get_book_service(
        book_repo: Annotated[BookRepository, Depends(get_book_repository)],
        ol_client: Annotated[OpenLibraryClient, Depends(get_openlibrary_client)],
) -> BookService:
    """
    Создать BookService с внедренными зависимостями.

    FastAPI автоматически разрешит все зависимости:
    1. get_db() создаст AsyncSession
    2. get_book_repository() создаст BookRepository с session
    3. get_openlibrary_client() вернет singleton клиент
    4. Все внедрится в BookService
    """
    return BookService(
        book_repository=book_repo,
        openlibrary_client=ol_client,
    )


# ========== TYPE ALIASES ДЛЯ УДОБСТВА ==========

# Можно использовать в роутерах так:
# async def my_route(service: BookServiceDep):
BookServiceDep = Annotated[BookService, Depends(get_book_service)]
BookRepoDep = Annotated[BookRepository, Depends(get_book_repository)]
DbSessionDep = Annotated[AsyncSession, Depends(get_db)]