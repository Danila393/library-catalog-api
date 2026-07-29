"""add trigram indexes for book search

Revision ID: 9e2c8c25d832
Revises: 3263f9e43942
Create Date: 2026-07-30 03:18:34.241931

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '9e2c8c25d832'
down_revision: Union[str, Sequence[str], None] = '3263f9e43942'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Добавить триграммные индексы для поиска книг."""

    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.drop_index(
        op.f("ix_books_title"),
        table_name="books",
    )
    op.drop_index(
        op.f("ix_books_author"),
        table_name="books",
    )

    op.create_index(
        "ix_books_title_trgm",
        "books",
        ["title"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"title": "gin_trgm_ops"},
    )
    op.create_index(
        "ix_books_author_trgm",
        "books",
        ["author"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"author": "gin_trgm_ops"},
    )


def downgrade() -> None:
    """Вернуть обычные B-tree индексы."""

    op.drop_index(
        "ix_books_author_trgm",
        table_name="books",
    )
    op.drop_index(
        "ix_books_title_trgm",
        table_name="books",
    )

    op.create_index(
        op.f("ix_books_author"),
        "books",
        ["author"],
        unique=False,
    )
    op.create_index(
        op.f("ix_books_title"),
        "books",
        ["title"],
        unique=False,
    )
