import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from .logging_context import REQUEST_ID_HEADER, request_id_var


logger = logging.getLogger(__name__)


class AppException(Exception):
    """Базовое исключение приложения."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundException(AppException):
    """Ресурс не найден."""

    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} with id '{identifier}' not found",
            status_code=404,
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Обработчики исключений."""

    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request,
        exc: AppException,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "detail": "Request validation failed",
                "errors": jsonable_encoder(exc.errors()),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
            request: Request,
            exc: Exception,
    ) -> JSONResponse:
        request_id = getattr(
            request.state,
            "request_id",
            request_id_var.get(),
        )
        token = request_id_var.set(request_id)

        try:
            logger.error(
                "Unhandled exception during %s %s",
                request.method,
                request.url.path,
                exc_info=exc,
                extra={
                    "http_method": request.method,
                    "http_path": request.url.path,
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                },
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"},
                headers={REQUEST_ID_HEADER: request_id},
            )
        finally:
            request_id_var.reset(token)