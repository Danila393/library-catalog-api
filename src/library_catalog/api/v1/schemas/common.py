from typing import Generic, Self, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Параметры пагинации."""

    page: int = Field(1, ge=1, description="Номер страницы")
    page_size: int = Field(20, ge=1, le=100, description="Размер страницы")

    @property
    def offset(self) -> int:
        """Вычислить offset для SQL."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Limit для SQL."""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic схема для пагинированных ответов."""

    items: list[T]
    total: int = Field(..., description="Всего элементов")
    page: int = Field(..., description="Текущая страница")
    page_size: int = Field(..., description="Размер страницы")
    pages: int = Field(..., description="Всего страниц")

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        pagination: PaginationParams,
    ) -> Self:
        """Создать пагинированный ответ."""
        pages = (total + pagination.page_size - 1) // pagination.page_size

        return cls(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            pages=pages,
        )


class HealthCheckResponse(BaseModel):
    """Схема для health check."""

    status: str = "healthy"
    database: str = "connected"
