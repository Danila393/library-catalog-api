from uuid import uuid4

from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.requests import Request
from starlette.responses import Response

from ...core.logging_context import REQUEST_ID_HEADER, request_id_var


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

        try:
            response = await call_next(request)
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            request_id_var.reset(token)