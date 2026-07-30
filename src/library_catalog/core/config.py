from typing import Literal
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Library Catalog API"
    environment: Literal["development", "staging", "production"]
    debug: bool

    # БД
    database_url: PostgresDsn
    database_pool_size: int = 20
    database_pool_max_overflow: int = 10
    database_pool_timeout: float = 30.0
    database_pool_recycle: int = 1800

    # API
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    log_format: Literal["text", "json"] = "text"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    cors_origins: list[str] = ["*"]

    # Внешние API
    openlibrary_base_url: str = "https://openlibrary.org"
    openlibrary_timeout: float = 10.0
    openlibrary_max_connections: int = 20
    openlibrary_max_keepalive_connections: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


    @property
    def database_url_str(self) -> str:
        return str(self.database_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()