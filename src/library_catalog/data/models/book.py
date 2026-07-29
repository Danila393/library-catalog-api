import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ...core.database import Base


class Book(Base):
    __tablename__ = "books"

    __table_args__ = (
        Index(
            "ix_books_title_trgm",
            "title",
            postgresql_using="gin",
            postgresql_ops={"title": "gin_trgm_ops"},
        ),
        Index(
            "ix_books_author_trgm",
            "author",
            postgresql_using="gin",
            postgresql_ops={"author": "gin_trgm_ops"},
        ),
    )

    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    author: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )

    year: Mapped[int] = mapped_column(
        index=True,
        nullable=False
    )

    genre: Mapped[str] = mapped_column(
        String(100),
        index=True,
    )

    pages: Mapped[int] = mapped_column(
        nullable=False
    )

    available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    isbn: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
    )

    description: Mapped[str | None] = mapped_column(Text)

    extra: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(), # Автоматически ставит текущее время базы при создании
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(), # Автоматически обновляет время при любом изменении строки
    )


    def __repr__(self) -> str:
        return f"<Book(id={self.book_id}, title='{self.title}')>"

