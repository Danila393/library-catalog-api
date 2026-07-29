from pydantic import BaseModel, ConfigDict, Field


class OpenLibrarySearchDoc(BaseModel):
    """Документ из поиска Open Library."""

    title: str
    author_name: list[str] | None = Field(None, alias="author_name")
    cover_i: int | None = Field(None, alias="cover_i")
    subject: list[str] | None = None
    publisher: list[str] | None = None
    language: list[str] | None = None
    ratings_average: float | None = Field(None, alias="ratings_average")

    model_config = ConfigDict(populate_by_name=True)


class OpenLibrarySearchResponse(BaseModel):
    """Ответ от /search.json"""

    numFound: int
    docs: list[OpenLibrarySearchDoc]