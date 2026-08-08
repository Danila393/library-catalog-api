from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from library_catalog.core.database import get_db
from library_catalog.main import app


@pytest.fixture
def database() -> AsyncMock:
    return AsyncMock()


@pytest_asyncio.fixture
async def health_client(
    database: AsyncMock,
) -> AsyncIterator[AsyncClient]:
    async def override_get_db() -> AsyncIterator[AsyncMock]:
        yield database

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(
        app=app,
        raise_app_exceptions=False,
    )

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_health_returns_200_when_database_is_available(
    health_client: AsyncClient,
    database: AsyncMock,
) -> None:
    response = await health_client.get("/api/v1/health/")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "database": "connected",
    }
    database.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_health_returns_503_when_database_is_unavailable(
    health_client: AsyncClient,
    database: AsyncMock,
) -> None:
    database.execute.side_effect = RuntimeError("database connection failed")

    response = await health_client.get("/api/v1/health/")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Database is unavailable",
    }
