from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse




class AppException(Exception):
    """Базовое исключение приложения."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundException(AppException):
    """Ресурс не найден."""

    def __init__(self, resource: str, identifier: any):
        super().__init__(
            message=f"{resource} with id '{identifier}' not found",
            status_code=404,
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Обработчики исключений."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )