from pydantic import BaseModel, Field, ConfigDict

from ....domain.dto.book import (
    BookCreateDTO,
    BookDTO,
    BookUpdateDTO
)




class BookCreate(BookCreateDTO):
    """Схема для создания книги."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Clean Code",
                    "author": "Robert Martin",
                    "year": 2008,
                    "genre": "Programming",
                    "pages": 464,
                    "isbn": "978-0132350884",
                    "description": (
                        "A Handbook of Agile Software Craftsmanship"
                     ),
                }
            ]
        }
    )


class BookUpdate(BookUpdateDTO):
    """Схема для обновления книги (все поля опциональны)."""


class ShowBook(BookDTO):
    """Схема для отображения книги (response)."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "book_id": "123e4567-e89b-12d3-a456-426614174000",
                    "title": "Clean Code",
                    "author": "Robert Martin",
                    "year": 2008,
                    "genre": "Programming",
                    "pages": 464,
                    "available": True,
                    "isbn": "978-0132350884",
                    "description": (
                        "A Handbook of Agile Software Craftsmanship"
                    ),
                    "extra": {
                        "cover_url": (
                            "https://covers.openlibrary.org/b/id/123-L.jpg"
                        ),
                        "subjects": [
                            "Computer Science",
                            "Software Engineering",
                        ],
                    },
                    "created_at": "2024-01-01T12:00:00",
                    "updated_at": "2024-01-01T12:00:00",
                }
            ]
        },
    )


class BookFilters(BaseModel):
    """Фильтры для поиска книг."""
    title: str | None = Field(None, description="Поиск по названию (частичное совпадение)")
    author: str | None = Field(None, description="Поиск по автору (частичное совпадение)")
    genre: str | None = Field(None, description="Точное совпадение жанра")
    year: int | None = Field(None, description="Точное совпадение года")
    available: bool | None = Field(None, description="Фильтр по доступности")