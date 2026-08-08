from fastapi import APIRouter, status
from sqlalchemy import text

from ....core.exceptions import DatabaseUnavailableException
from ...dependencies import DbSessionDep
from ..schemas.common import HealthCheckResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "/",
    response_model=HealthCheckResponse,
    summary="Health Check",
    description="Проверить состояние сервиса и подключение к БД",
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Database is unavailable",
        },
    },
)
async def health_check(db: DbSessionDep) -> HealthCheckResponse:
    """
    Проверить здоровье сервиса.

    Проверяет:
    - Сервис запущен
    - Подключение к БД работает
    """
    # Простой запрос к БД для проверки соединения
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        raise DatabaseUnavailableException from exc

    return HealthCheckResponse(
        status="healthy",
        database="connected",
    )
