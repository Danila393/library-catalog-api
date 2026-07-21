from fastapi import APIRouter
from sqlalchemy import text

from ..schemas.common import HealthCheckResponse
from ...dependencies import DbSessionDep

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "/",
    response_model=HealthCheckResponse,
    summary="Health Check",
    description="Проверить состояние сервиса и подключение к БД",
)
async def health_check(db: DbSessionDep):
    """
    Проверить здоровье сервиса.

    Проверяет:
    - Сервис запущен
    - Подключение к БД работает
    """
    # Простой запрос к БД для проверки соединения
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return HealthCheckResponse(
        status="healthy",
        database=db_status,
    )