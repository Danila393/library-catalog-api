from uuid import UUID
from ...api.v1.schemas.book import BookCreate, BookUpdate, ShowBook
from ...data.repositories.book_repository import BookRepository
from ...external.openlibrary.client import OpenLibraryClient
from ..exceptions import *
from ..mappers.book_mapper import BookMapper


class BookService:
    """
    Сервис для работы с книгами.

    Содержит всю бизнес-логику приложения.
    """

    def __init__(
            self,
            book_repository: BookRepository,
            openlibrary_client: OpenLibraryClient,
    ):
        self.book_repo = book_repository
        self.ol_client = openlibrary_client

    async def create_book(self, book_data: BookCreate) -> ShowBook:
        """
        Создать новую книгу с обогащением из Open Library.

        Бизнес-правила:
        - Год не в будущем
        - Страницы > 0
        - ISBN уникален (если указан)

        Args:
            book_data: Данные для создания

        Returns:
            ShowBook: Созданная книга

        Raises:
            InvalidYearException: Если год невалиден
            InvalidPagesException: Если страницы <= 0
            BookAlreadyExistsException: Если ISBN уже существует
        """
        # 1. Валидация бизнес-правил
        self._validate_book_data(book_data)

        # 2. Проверка уникальности ISBN
        if book_data.isbn:
            existing = await self.book_repo.find_by_isbn(book_data.isbn)
            if existing:
                raise BookAlreadyExistsException(book_data.isbn)

        # 3. Обогащение данных из Open Library
        extra = await self._enrich_book_data(book_data)

        # 4. Создание в БД
        book = await self.book_repo.create(
            title=book_data.title,
            author=book_data.author,
            year=book_data.year,
            genre=book_data.genre,
            pages=book_data.pages,
            isbn=book_data.isbn,
            description=book_data.description,
            extra=extra,
        )

        # 5. Маппинг в DTO
        return BookMapper.to_show_book(book)

    async def get_book(self, book_id: UUID) -> ShowBook:
        """
        Получить книгу по ID.

        Raises:
            BookNotFoundException: Если книга не найдена
        """
        book = await self.book_repo.get_by_id(book_id)
        if book is None:
            raise BookNotFoundException(book_id)

        return BookMapper.to_show_book(book)

    async def update_book(
            self,
            book_id: UUID,
            book_data: BookUpdate,
    ) -> ShowBook:
        """
        Обновить книгу.

        Обновляются только переданные поля.
        """
        # Проверить существование
        existing = await self.book_repo.get_by_id(book_id)
        if existing is None:
            raise BookNotFoundException(book_id)

        # Валидация если обновляется год/страницы
        if book_data.year is not None:
            self._validate_year(book_data.year)
        if book_data.pages is not None:
            self._validate_pages(book_data.pages)

        # Обновить
        updated = await self.book_repo.update(
            book_id,
            **book_data.dict(exclude_unset=True)
        )

        return BookMapper.to_show_book(updated)

    async def delete_book(self, book_id: UUID) -> None:
        """
        Удалить книгу.

        Raises:
            BookNotFoundException: Если книга не найдена
        """
        deleted = await self.book_repo.delete(book_id)
        if not deleted:
            raise BookNotFoundException(book_id)

    async def search_books(
            self,
            title: str | None = None,
            author: str | None = None,
            genre: str | None = None,
            year: int | None = None,
            available: bool | None = None,
            limit: int = 20,
            offset: int = 0,
    ) -> tuple[list[ShowBook], int]:
        """
        Поиск книг с фильтрацией и пагинацией.

        Returns:
            tuple: (список книг, общее количество)
        """
        # Получить книги
        books = await self.book_repo.find_by_filters(
            title=title,
            author=author,
            genre=genre,
            year=year,
            available=available,
            limit=limit,
            offset=offset,
        )

        # Подсчитать общее количество
        total = await self.book_repo.count_by_filters(
            title=title,
            author=author,
            genre=genre,
            year=year,
            available=available,
        )

        return BookMapper.to_show_books(books), total

    # ========== ПРИВАТНЫЕ МЕТОДЫ ==========

    def _validate_book_data(self, data: BookCreate) -> None:
        """Валидация бизнес-правил для новой книги."""
        self._validate_year(data.year)
        self._validate_pages(data.pages)

    def _validate_year(self, year: int) -> None:
        """Проверить что год валиден."""
        from datetime import datetime

        current_year = datetime.now().year
        if year < 1000 or year > current_year:
            raise InvalidYearException(year)

    def _validate_pages(self, pages: int) -> None:
        """Проверить что количество страниц валидно."""
        if pages <= 0:
            raise InvalidPagesException(pages)

    async def _enrich_book_data(
            self,
            book_data: BookCreate
    ) -> dict | None:
        """
        Обогатить данные книги из Open Library.

        Не выбрасывает исключение если API недоступен.
        """
        try:
            extra = await self.ol_client.enrich(
                title=book_data.title,
                author=book_data.author,
                isbn=book_data.isbn,
            )
            return extra if extra else None
        except OpenLibraryException:
            # Логируем но не прерываем создание книги
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                "Failed to enrich book data from Open Library",
                extra={"title": book_data.title, "author": book_data.author}
            )
            return None