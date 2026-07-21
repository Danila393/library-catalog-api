from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from ..schemas.book import (
    BookCreate,
    BookUpdate,
    ShowBook,
)
from ..schemas.common import PaginatedResponse, PaginationParams
from ...dependencies import BookServiceDep

router = APIRouter(prefix="/books", tags=["Books"])


@router.post(
    "/",
    response_model=ShowBook,
    status_code=status.HTTP_201_CREATED,
    summary="Создать книгу",
    description="Создать новую книгу в каталоге с автоматическим обогащением из Open Library",
)
async def create_book(
        book_data: BookCreate,
        service: BookServiceDep,
):
    """
    Создать новую книгу.

    Автоматически обогащает данные из Open Library API:
    - Обложка книги
    - Темы/subjects
    - Издатель
    - Рейтинг

    Если Open Library недоступен, книга все равно будет создана.
    """
    return await service.create_book(book_data)


@router.get(
    "/",
    response_model=PaginatedResponse[ShowBook],
    summary="Получить список книг",
    description="Получить список книг с фильтрацией и пагинацией",
)
async def get_books(
        service: BookServiceDep,
        pagination: Annotated[PaginationParams, Depends()],
        title: str | None = Query(None, description="Поиск по названию"),
        author: str | None = Query(None, description="Поиск по автору"),
        genre: str | None = Query(None, description="Фильтр по жанру"),
        year: int | None = Query(None, description="Фильтр по году"),
        available: bool | None = Query(None, description="Фильтр по доступности"),
):
    """
    Получить список книг с фильтрацией.

    Поддерживаемые фильтры:
    - title: частичное совпадение (регистронезависимо)
    - author: частичное совпадение (регистронезависимо)
    - genre: точное совпадение
    - year: точное совпадение
    - available: True/False

    Пагинация:
    - page: номер страницы (начиная с 1)
    - page_size: размер страницы (1-100, по умолчанию 20)
    """
    books, total = await service.search_books(
        title=title,
        author=author,
        genre=genre,
        year=year,
        available=available,
        limit=pagination.limit,
        offset=pagination.offset,
    )

    return PaginatedResponse.create(books, total, pagination)


@router.get(
    "/{book_id}",
    response_model=ShowBook,
    summary="Получить книгу",
    description="Получить информацию о конкретной книге по ID",
)
async def get_book(
        book_id: UUID,
        service: BookServiceDep,
):
    """
    Получить книгу по ID.

    Returns:
        ShowBook: Полная информация о книге

    Raises:
        404: Книга не найдена
    """
    return await service.get_book(book_id)


@router.patch(
    "/{book_id}",
    response_model=ShowBook,
    summary="Обновить книгу",
    description="Частичное обновление книги (передаются только изменяемые поля)",
)
async def update_book(
        book_id: UUID,
        book_data: BookUpdate,
        service: BookServiceDep,
):
    """
    Обновить книгу.

    Передаются только те поля, которые нужно изменить.
    Остальные поля остаются без изменений.

    Returns:
        ShowBook: Обновленная книга

    Raises:
        404: Книга не найдена
        400: Невалидные данные
    """
    return await service.update_book(book_id, book_data)


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить книгу",
    description="Удалить книгу из каталога",
)
async def delete_book(
        book_id: UUID,
        service: BookServiceDep,
):
    """
    Удалить книгу.

    Raises:
        404: Книга не найдена
    """
    await service.delete_book(book_id)