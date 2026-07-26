from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BookBaseDTO(BaseModel):
    """Общие данные книги."""

    title: str = Field(..., min_length=1, max_length=500)
    author: str = Field(..., min_length=1, max_length=300)
    year: int = Field(..., ge=1000, le=2100)
    genre: str = Field(..., min_length=1, max_length=100)
    pages: int = Field(..., gt=0)


class BookCreateDTO(BookBaseDTO):
    """Данные для создания книги."""

    isbn: str | None = Field(None, min_length=10, max_length=20)
    description: str | None = Field(None, max_length=5000)

    @field_validator("isbn")
    @classmethod
    def validate_isbn(cls, value: str | None) -> str | None:
        """Валидация формата ISBN."""
        if value is None:
            return value

        # Удалить дефисы
        clean = value.replace('-', '').replace(' ', '')

        # Проверить что только цифры (и X для ISBN-10)
        if not clean.replace("X", '').isdigit():
            raise ValueError("ISBN может содержать только цифры.")

        # Проверить длину
        if len(clean) not in (10, 13):
            raise ValueError("ISBN должен состоять из 10 или 13 чисел.")

        return value


class BookUpdateDTO(BaseModel):
    """Данные для частичного обновления книги (все поля опциональны)."""

    title: str | None = Field(None, min_length=1, max_length=500)
    author: str | None = Field(None, min_length=1, max_length=300)
    year: int | None = Field(None, ge=1000, le=2100)
    genre: str | None = Field(None, min_length=1, max_length=100)
    pages: int | None = Field(None, gt=0)
    available: bool | None = None
    isbn: str | None = None
    description: str | None = None


class BookDTO(BookBaseDTO):
    """Полные данные книги, возвращаемые сервисом."""

    book_id: UUID
    available: bool
    isbn: str | None
    description: str | None
    extra: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)