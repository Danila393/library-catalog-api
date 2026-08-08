from datetime import datetime
from typing import Any, TypeAlias
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

BookExtra: TypeAlias = dict[str, Any]


def _validate_isbn_format(value: str | None) -> str | None:
    """Проверить формат ISBN."""

    if value is None:
        return value

    clean = value.replace("-", "").replace(" ", "")

    if not clean.replace("X", "").isdigit():
        raise ValueError("ISBN может содержать только цифры.")

    if len(clean) not in (10, 13):
        raise ValueError("ISBN должен состоять из 10 или 13 символов.")

    return value


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
        """Проверить ISBN при создании книги."""
        return _validate_isbn_format(value)


class BookUpdateDTO(BaseModel):
    """Данные для частичного обновления книги (все поля опциональны)."""

    title: str | None = Field(None, min_length=1, max_length=500)
    author: str | None = Field(None, min_length=1, max_length=300)
    year: int | None = Field(None, ge=1000, le=2100)
    genre: str | None = Field(None, min_length=1, max_length=100)
    pages: int | None = Field(None, gt=0)
    available: bool | None = None
    isbn: str | None = Field(
        None,
        min_length=10,
        max_length=20,
    )
    description: str | None = None

    @field_validator("isbn")
    @classmethod
    def validate_isbn(cls, value: str | None) -> str | None:
        """Проверить ISBN при обновлении книги."""
        return _validate_isbn_format(value)


class BookDTO(BookBaseDTO):
    """Полные данные книги, возвращаемые сервисом."""

    book_id: UUID
    available: bool
    isbn: str | None
    description: str | None
    extra: BookExtra | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
