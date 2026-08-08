import logging
from time import perf_counter
from uuid import uuid4

from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.requests import Request
from starlette.responses import Response

from ...core.logging_context import REQUEST_ID_HEADER, request_id_var

logger = logging.getLogger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Добавить уникальный идентификатор каждому HTTP-запросу."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = str(uuid4())
        request.state.request_id = request_id
        token = request_id_var.set(request_id)

        started_at = perf_counter()

        try:
            response = await call_next(request)
            response.headers[REQUEST_ID_HEADER] = request_id

            duration_ms = round(
                (perf_counter() - started_at) * 1000,
                2,
            )

            logger.info(
                "%s %s completed with status %s in %.2f ms",
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
                extra={
                    "http_method": request.method,
                    "http_path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )

            return response
        finally:
            request_id_var.reset(token)
